/* INSTAR page 56 lab. Public hex only. No preimage search. */
(function () {
  const HEX =
    "36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4";
  const LINES = [
    "36367763ab73783c7af284446c",
    "59466b4cd653239a311cb7116",
    "d4618dee09a8425893dc7500b",
    "464fdaf1672d7bef5e891c6e227",
    "4568926a49fb4f45132c2a8b4",
  ];
  const ONION_V2 = "gy3hoy2zizvuzvdb";
  const ABC = "abcdefghijklmnopqrstuvwxyz234567";

  function hexBytes(hex) {
    const out = [];
    for (let i = 0; i < hex.length; i += 2) out.push(parseInt(hex.slice(i, i + 2), 16));
    return out;
  }

  function b32encode(bytes) {
    let bits = 0;
    let value = 0;
    let out = "";
    for (let i = 0; i < bytes.length; i++) {
      value = (value << 8) | bytes[i];
      bits += 8;
      while (bits >= 5) {
        out += ABC[(value >>> (bits - 5)) & 31];
        bits -= 5;
      }
    }
    if (bits > 0) out += ABC[(value << (5 - bits)) & 31];
    return out;
  }

  function first8(lines) {
    return lines.map(function (ln) {
      return ln.slice(0, 8);
    }).join("");
  }

  function after8(lines) {
    return lines.map(function (ln) {
      return ln.slice(8);
    }).join("");
  }

  function chunks(hex, n) {
    const out = [];
    for (let i = 0; i < hex.length; i += n) out.push(hex.slice(i, i + n));
    return out;
  }

  function onionFromExtract(hex40) {
    return b32encode(hexBytes(hex40).slice(0, 10));
  }

  function report() {
    const extract = first8(LINES);
    const leftover = after8(LINES);
    return {
      hex: HEX,
      lines: LINES,
      extract: extract,
      leftover: leftover,
      onionHost: onionFromExtract(extract),
      gcmKey: leftover.slice(0, 64),
      gcmNonce: leftover.slice(64),
      wrap8x16: first8(chunks(HEX, 16)),
      wrap4x32: first8(chunks(HEX, 32)),
      vtIndex: hexBytes(HEX).indexOf(0x0b),
    };
  }

  window.INSTAR_PAGE56 = {
    HEX: HEX,
    LINES: LINES,
    ONION_V2: ONION_V2,
    hexBytes: hexBytes,
    b32encode: b32encode,
    first8: first8,
    after8: after8,
    chunks: chunks,
    onionFromExtract: onionFromExtract,
    report: report,
  };
})();
