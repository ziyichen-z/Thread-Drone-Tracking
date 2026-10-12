using System;
using System.Text;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// BC-P2-10: the serialization boundary of every artifact this tool
    /// writes must be standard JSON (RFC 8259).
    ///
    /// `JsonUtility` prints a non-finite float as the bare tokens `NaN`,
    /// `Infinity` or `-Infinity`, which no strict parser accepts. Those
    /// tokens carry one meaning here — "this number is not available for
    /// this record" (an unprojectable truth box has no `min_side_px` and no
    /// edge margins) — and the neighbouring `geometrically_visible` /
    /// `target_box_status` fields already say why. So the boundary writes
    /// JSON `null`; a finite sentinel is never substituted, because that
    /// would disguise an unavailable value as a measurement.
    ///
    /// The rewrite is a scanner, not a text search: it tracks string
    /// literals (including escapes) and only touches value tokens, so a
    /// string that happens to contain "NaN" or "null" is preserved. The
    /// reverse direction exists so a committed artifact round-trips back
    /// into the same float values it was produced from.
    /// </summary>
    public static class Scene006Json
    {
        const string NullToken = "null";
        const string NaNToken = "NaN";
        const string PositiveInfinityToken = "Infinity";
        const string NegativeInfinityToken = "-Infinity";

        /// <summary>
        /// `JsonUtility` output → standard JSON: every bare non-finite
        /// number token becomes `null`.
        /// </summary>
        public static string ToStrictJson(string json) =>
            Rewrite(json, strict: true);

        /// <summary>
        /// Standard JSON → the `JsonUtility` dialect: every bare `null`
        /// becomes `NaN`, so `JsonUtility.FromJson` recovers the original
        /// unavailable-number semantics instead of silently reading 0.
        ///
        /// Callers that use `null` for a non-numeric field (the selection
        /// artifact's `selected_tick` sentinel) must translate that field
        /// before calling this.
        /// </summary>
        public static string FromStrictJson(string json) =>
            Rewrite(json, strict: false);

        /// <summary>
        /// Fail-closed check used right before a write: true when a bare
        /// non-finite token is still present outside a string literal.
        /// </summary>
        public static bool ContainsNonFiniteToken(string json)
        {
            if (json == null) throw new ArgumentNullException(nameof(json));
            bool inString = false;
            for (int index = 0; index < json.Length; index++)
            {
                char character = json[index];
                if (inString)
                {
                    if (character == '\\') { index++; continue; }
                    if (character == '"') inString = false;
                    continue;
                }
                if (character == '"') { inString = true; continue; }
                if (Matches(json, index, NaNToken)
                    || Matches(json, index, NegativeInfinityToken)
                    || Matches(json, index, PositiveInfinityToken))
                {
                    return true;
                }
            }
            return false;
        }

        static string Rewrite(string json, bool strict)
        {
            if (json == null) throw new ArgumentNullException(nameof(json));
            var builder = new StringBuilder(json.Length);
            bool inString = false;
            for (int index = 0; index < json.Length; index++)
            {
                char character = json[index];
                if (inString)
                {
                    builder.Append(character);
                    if (character == '\\' && index + 1 < json.Length)
                    {
                        builder.Append(json[++index]);
                        continue;
                    }
                    if (character == '"') inString = false;
                    continue;
                }
                if (character == '"')
                {
                    inString = true;
                    builder.Append(character);
                    continue;
                }
                if (strict)
                {
                    if (Replace(json, ref index, builder, NaNToken, NullToken)
                        || Replace(
                            json, ref index, builder,
                            NegativeInfinityToken, NullToken)
                        || Replace(
                            json, ref index, builder,
                            PositiveInfinityToken, NullToken))
                    {
                        continue;
                    }
                }
                else if (Replace(
                    json, ref index, builder, NullToken, NaNToken))
                {
                    continue;
                }
                builder.Append(character);
            }
            if (inString)
            {
                throw new InvalidOperationException(
                    "unterminated JSON string literal; refusing to rewrite");
            }
            return builder.ToString();
        }

        static bool Replace(
            string json,
            ref int index,
            StringBuilder builder,
            string token,
            string replacement)
        {
            if (!Matches(json, index, token)) return false;
            builder.Append(replacement);
            index += token.Length - 1;
            return true;
        }

        static bool Matches(string json, int index, string token)
        {
            if (index + token.Length > json.Length) return false;
            for (int offset = 0; offset < token.Length; offset++)
            {
                if (json[index + offset] != token[offset]) return false;
            }
            return true;
        }
    }
}
