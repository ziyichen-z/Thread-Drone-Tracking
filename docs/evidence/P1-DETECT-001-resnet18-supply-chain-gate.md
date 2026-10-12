# P1-DETECT-001 ResNet18 supply-chain gate

Date: 2026-07-28  
Owner: Codex  
Verdict: `BLOCKED_LICENSE_AMBIGUITY_BEFORE_MODEL_USE`

## Downloaded artifact identity

The user explicitly authorized the accepted
`ResNet18_Weights.IMAGENET1K_V1` download and implementation on 2026-07-28.
Codex downloaded the artifact from the exact URL exposed by torchvision
0.28.0:

- URL: `https://download.pytorch.org/models/resnet18-f37072fd.pth`
- local ignored path: `runtime/models/resnet18-f37072fd.pth`
- size: `46,830,571` bytes
- SHA-256:
  `f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`
- torchvision enum: `ResNet18_Weights.IMAGENET1K_V1`
- frozen preprocessing: resize 256, center crop 224, bilinear interpolation,
  mean `[0.485, 0.456, 0.406]`, standard deviation
  `[0.229, 0.224, 0.225]`

The artifact was hashed as an opaque file. It was not deserialized or passed
to `torch.load`, `load_state_dict`, or a torchvision model constructor.

## License check

The accepted proposal's Codex Round 2 binding requires affirmative evidence
that covers the weight artifact itself before first model use. It explicitly
forbids treating torchvision's BSD-3-Clause code license as the weight
license.

The official torchvision model documentation and official repository both
state that pretrained models may have their own licenses or terms derived
from their training datasets and that the user is responsible for determining
whether use is permitted:

- `https://docs.pytorch.org/vision/stable/models.html`
- `https://github.com/pytorch/vision#pre-trained-model-license`

Neither source supplies an affirmative license grant specifically covering
`resnet18-f37072fd.pth`. The ImageNet dataset terms are not an affirmative
license for this separately distributed derived weight artifact.

Therefore the binding evidence requirement is not satisfied. The
implementation gate fails closed before model use. No scouting, model smoke,
dependent runtime implementation, qualification run, or successor-rate batch
may begin under this frozen model decision.

## Required user/design decision

One of the following is required before implementation can resume:

1. provide authoritative affirmative license evidence that explicitly covers
   this weight artifact and the intended project use; or
2. authorize a proposal revision selecting a different frozen appearance
   embedding weight with an explicit artifact license.

Changing the embedding model without a proposal revision would alter the
accepted model-decision logic and is not authorized by the download consent.
