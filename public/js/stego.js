/* LSB extract + strings. Educational OutGuess-class habit, not the OutGuess binary. */
(function () {
  function bitsToBytes(bits) {
    const out = [];
    for (let i = 0; i + 8 <= bits.length; i += 8) {
      let v = 0;
      for (let j = 0; j < 8; j++) v = (v << 1) | bits[i + j];
      out.push(v);
    }
    return new Uint8Array(out);
  }
  function bitsFromRgba(data, channel, bit) {
    channel = Math.max(0, Math.min(2, Number(channel) || 0));
    bit = Math.max(0, Math.min(7, Number(bit) || 0));
    const bits = [];
    for (let i = 0; i < data.length; i += 4) {
      bits.push((data[i + channel] >> bit) & 1);
    }
    return bits;
  }
  function utf8FromBits(bits) {
    const bytes = bitsToBytes(bits);
    const zero = bytes.indexOf(0);
    const slice = zero >= 0 ? bytes.subarray(0, zero) : bytes.subarray(0, 4096);
    return new TextDecoder("utf-8", { fatal: false }).decode(slice);
  }
  function extractPlane(data, channel, bit) {
    return utf8FromBits(bitsFromRgba(data, channel, bit));
  }
  async function lsbExtract(file) {
    const url = URL.createObjectURL(file);
    try {
      const img = new Image();
      img.src = url;
      await img.decode();
      const c = document.createElement("canvas");
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      const ctx = c.getContext("2d", { willReadFrequently: true });
      ctx.drawImage(img, 0, 0);
      const data = ctx.getImageData(0, 0, c.width, c.height).data;
      return extractPlane(data, 0, 0);
    } finally {
      URL.revokeObjectURL(url);
    }
  }
  async function stringsDump(file, minLen) {
    const buf = new Uint8Array(await file.arrayBuffer());
    minLen = minLen || 6;
    const found = [];
    let cur = [];
    for (const b of buf) {
      if (b >= 32 && b < 127) cur.push(b);
      else {
        if (cur.length >= minLen) found.push(String.fromCharCode.apply(null, cur));
        cur = [];
      }
    }
    if (cur.length >= minLen) found.push(String.fromCharCode.apply(null, cur));
    return found;
  }
  async function drawBitPlane(file, canvas, channel, bit) {
    channel = Math.max(0, Math.min(2, Number(channel) || 0));
    bit = Math.max(0, Math.min(7, Number(bit) || 0));
    const url = URL.createObjectURL(file);
    try {
      const img = new Image();
      img.src = url;
      await img.decode();
      const src = document.createElement("canvas");
      src.width = img.naturalWidth;
      src.height = img.naturalHeight;
      const sctx = src.getContext("2d", { willReadFrequently: true });
      sctx.drawImage(img, 0, 0);
      const data = sctx.getImageData(0, 0, src.width, src.height).data;
      const out = sctx.createImageData(src.width, src.height);
      for (let i = 0; i < data.length; i += 4) {
        const v = (data[i + channel] >> bit) & 1;
        out.data[i] = v ? 196 : 8;
        out.data[i + 1] = v ? 163 : 7;
        out.data[i + 2] = v ? 106 : 5;
        out.data[i + 3] = 255;
      }
      canvas.width = src.width;
      canvas.height = src.height;
      canvas.getContext("2d").putImageData(out, 0, 0);
    } finally {
      URL.revokeObjectURL(url);
    }
  }
  window.INSTAR_STEGO = { lsbExtract, stringsDump, drawBitPlane, extractPlane };
})();
