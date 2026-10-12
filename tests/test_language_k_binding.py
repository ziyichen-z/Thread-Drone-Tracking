"""AC-10: measured K provenance and live model identity reject mismatches."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller.language_loop import KReceipt, LanguageSession, SessionConfig, ConfigMismatch, build_parser, _run_session
from controller.language_selector import HttpAdapter, ScriptedAdapter, SelectorError, sha256_file
from tools.language_latency import build_receipt_document
from tests.test_language_selector import _ServerCase, _raw, NONE


class ReceiptBindingTests(_ServerCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.identity = dict(ScriptedAdapter([]).identity, backend='http', device='cuda',
                             weights_sha256='a' * 64, base_repo_revision='b' * 40)
        common = {'verdict':'OK', 'hz':5.0, 'retained_frame_count':128, 'model_form':'c2-adapter'}
        self.mac = dict(common, host='mac', backend='local-hf', tier='B', p95_s=8.0,
                        model_identity=dict(self.identity,backend='local-hf',device='mps'))
        self.gpu = dict(common, host='5060',backend='http',tier='A',p95_s=2.0,
                        model_identity=self.identity,transport={'endpoint':'http://127.0.0.1:8760'})
        self.document = build_receipt_document(self.mac, self.gpu)
        self.document['source_reports'] = {}
        for host, report in [('mac',self.mac),('5060',self.gpu)]:
            path = self.root/f'{host}.json'
            path.write_text(json.dumps(report))
            self.document['source_reports'][host] = {'path':str(path),'sha256':sha256_file(path)}
        self.receipt_path = self.root/'k.json'
        self.receipt_path.write_text(json.dumps(self.document))
        self.receipt = KReceipt.from_document(self.document)

    def config(self, receipt=None, identity=None):
        return SessionConfig(session_id='fixture',session_root=self.root/'sessions',runtime=self.root/'runtime',
                             receipt=receipt or self.receipt,
                             adapter=ScriptedAdapter([],identity=identity or self.identity))

    def test_changed_weights_refused_before_creating_session(self):
        with self.assertRaisesRegex(ConfigMismatch,'adapter identity'):
            LanguageSession(self.config(identity=dict(self.identity,weights_sha256='c'*64)))
        self.assertFalse((self.root/'sessions').exists())
        self.assertFalse((self.root/'runtime').exists())

    def test_backend_form_prompt_base_and_device_mismatch_are_refused(self):
        for key, value in [('backend','replay'),('model_form','base'),('prompt_template_sha256','c'*64),
                           ('base_repo_revision','d'*40),('device','mps')]:
            with self.subTest(key=key), self.assertRaises(ConfigMismatch):
                LanguageSession(self.config(identity=dict(self.identity,**{key:value})))

    def test_changed_host_or_receipt_model_binding_is_refused(self):
        for change in [dict(host='mac'),dict(model_form='base'),dict(model_identity=dict(self.identity,weights_sha256='d'*64))]:
            with self.subTest(change=change), self.assertRaisesRegex(ConfigMismatch,'measurement binding'):
                LanguageSession(self.config(receipt=replace(self.receipt,**change)))

    def test_source_bytes_changed_even_if_json_meaning_is_same(self):
        path=Path(self.receipt.source_reports['5060']['path'])
        path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ConfigMismatch,'SHA changed'):
            LanguageSession(self.config())

    def test_missing_sources_and_changed_p95_are_refused(self):
        for receipt in [replace(self.receipt,source_reports={}),replace(self.receipt,p95_s=1.,k_ret=7)]:
            with self.assertRaises(ConfigMismatch):
                LanguageSession(self.config(receipt=receipt))

    def test_k_pub_cannot_override_frozen_constant(self):
        with self.assertRaises(ConfigMismatch):
            KReceipt.from_document(dict(self.document,k_pub=99))

    def test_cli_rejects_endpoint_or_backend_before_adapter_load(self):
        common=['run','--session-id','fixture','--session-root',str(self.root/'sessions'),
                '--runtime',str(self.root/'runtime'),'--k-receipt',str(self.receipt_path),
                '--model-form','c2-adapter']
        for extra in [['--backend','http','--server-url','http://127.0.0.2:8760'],['--backend','local-hf']]:
            args=build_parser().parse_args(common+extra)
            with patch('controller.language_loop._build_adapter') as load, self.assertRaises(ConfigMismatch):
                _run_session(args)
            load.assert_not_called()
        self.assertFalse((self.root/'sessions').exists())

    def test_measured_sources_and_current_service_can_create_session(self):
        from controller.language_loop import validate_measurement_sources
        self.assertEqual(validate_measurement_sources(self.receipt),self.gpu)
        # A fake adapter cannot bypass the real HTTP identity handshake.
        with self.assertRaisesRegex(ConfigMismatch,'live HTTP'):
            LanguageSession(self.config())

    def test_bound_real_http_session_initializes_without_model_queries(self):
        scripted=ScriptedAdapter([],identity=dict(self.identity,backend='local-hf'))
        url=self._serve(scripted)
        path=Path(self.document['source_reports']['5060']['path'])
        self.gpu['transport']['endpoint']=url
        path.write_text(json.dumps(self.gpu))
        self.document['source_reports']['5060']['sha256']=sha256_file(path)
        receipt=KReceipt.from_document(self.document)
        client=HttpAdapter(url,t_ret_s=receipt.t_ret_s,t_hard_s=60.,model_form=receipt.model_form,
                           weights_sha256=self.identity['weights_sha256'],base_repo_revision=self.identity['base_repo_revision'])
        session=LanguageSession(replace(self.config(receipt=receipt),adapter=client))
        self.addCleanup(session.close)
        self.assertEqual(session.state,'IDLE')
        self.assertEqual(scripted.calls,[])


class HttpIdentityBindingTests(_ServerCase):
    def setup_bound(self):
        scripted=ScriptedAdapter([_raw(NONE)],identity={'backend':'local-hf','model_form':'c2-adapter',
            'device':'cuda','weights_sha256':'a'*64,'base_repo_revision':'b'*40})
        url=self._serve(scripted)
        client=HttpAdapter(url,t_ret_s=3.,t_hard_s=6.,poll_interval_s=.01)
        expected=dict(scripted.identity,backend='http')
        client.bind_identity(expected)
        return scripted,client,expected

    def test_live_handshake_and_matching_query_succeed(self):
        scripted,client,expected=self.setup_bound()
        self.assertEqual(scripted.calls,[])
        self.assertEqual(client.identity,expected)
        self.assertEqual(client.predict_one('bound-1',self._image(),'the red car',False).raw_output,NONE)
        self.assertEqual(len(scripted.calls),1)

    def test_changed_service_is_rejected_before_inference_or_image_write(self):
        scripted,client,_=self.setup_bound()
        scripted.identity['weights_sha256']='c'*64
        with self.assertRaisesRegex(SelectorError,'MODEL_IDENTITY_MISMATCH'):
            client.predict_one('changed-1',self._image(),'the red car',False)
        self.assertTrue(client.fatal)
        self.assertEqual(scripted.calls,[])
        self.assertFalse((Path(self._directory.name)/'images'/'changed-1.jpg').exists())

    def test_missing_or_wrong_handshake_identity_is_not_trusted(self):
        calls=[]
        def opener(request,timeout):
            calls.append((request.method,timeout))
            return b'{"state":"idle"}'
        client=HttpAdapter('http://fixture',t_ret_s=3.,t_hard_s=6.,opener=opener)
        with self.assertRaisesRegex(SelectorError,'MODEL_IDENTITY_MISMATCH'):
            client.bind_identity(dict(client.identity,weights_sha256='a'*64))
        self.assertEqual(calls,[('GET',5.)])
        self.assertTrue(client.fatal)

    def test_identity_change_during_inference_never_returns_a_result(self):
        scripted,client,_=self.setup_bound()
        scripted._on_call=lambda *_:scripted.identity.update(weights_sha256='c'*64)
        with self.assertRaisesRegex(SelectorError,'MODEL_IDENTITY_MISMATCH'):
            client.predict_one('changed-during',self._image(),'the red car',False)
        self.runtime.join(1)
        self.assertEqual(len(scripted.calls),1)
        self.assertTrue(client.fatal)


if __name__=='__main__':
    unittest.main()
