/* Simple STFT spectrogram painter. opts: nfft, hop, gain. */
(function () {
  async function drawFile(file, canvas, opts) {
    const ctxA = new (window.AudioContext || window.webkitAudioContext)();
    const buf = await ctxA.decodeAudioData(await file.arrayBuffer());
    drawBuffer(buf, canvas, opts);
    ctxA.close();
  }
  function drawBuffer(buf, canvas, opts) {
    opts = opts || {};
    const data = buf.getChannelData(0);
    const w = (canvas.width = canvas.clientWidth * 2 || 1200);
    const h = (canvas.height = 440);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);
    let nfft = Number(opts.nfft) || 2048;
    if (nfft < 256) nfft = 256;
    nfft = 1 << Math.round(Math.log2(nfft));
    let hop = Number(opts.hop) || Math.floor(nfft / 4);
    if (hop < 32) hop = 32;
    const gain = Number(opts.gain) || 80;
    const cols = Math.min(w, Math.floor((data.length - nfft) / hop));
    for (let x = 0; x < cols; x++) {
      const off = x * hop;
      const re = new Float64Array(nfft);
      const im = new Float64Array(nfft);
      for (let i = 0; i < nfft; i++) {
        const win = 0.5 * (1 - Math.cos((2 * Math.PI * i) / (nfft - 1)));
        re[i] = (data[off + i] || 0) * win;
      }
      fft(re, im);
      for (let y = 0; y < h; y++) {
        const bin = Math.floor(((h - 1 - y) / h) * (nfft / 2));
        const mag = Math.log10(1 + Math.hypot(re[bin], im[bin]) * gain);
        const t = Math.min(1, mag / 1.8);
        const r = Math.floor(20 + t * 200);
        const g = Math.floor(10 + t * 140);
        const b = Math.floor(4 + t * 40);
        ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
        ctx.fillRect(x, y, 1, 1);
      }
    }
  }
  function fft(re, im) {
    const n = re.length;
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        const tr = re[i];
        re[i] = re[j];
        re[j] = tr;
        const ti = im[i];
        im[i] = im[j];
        im[j] = ti;
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = (-2 * Math.PI) / len;
      const wr0 = Math.cos(ang);
      const wi0 = Math.sin(ang);
      for (let i = 0; i < n; i += len) {
        let wr = 1;
        let wi = 0;
        for (let j = 0; j < len / 2; j++) {
          const ur = re[i + j];
          const ui = im[i + j];
          const vr = re[i + j + len / 2] * wr - im[i + j + len / 2] * wi;
          const vi = re[i + j + len / 2] * wi + im[i + j + len / 2] * wr;
          re[i + j] = ur + vr;
          im[i + j] = ui + vi;
          re[i + j + len / 2] = ur - vr;
          im[i + j + len / 2] = ui - vi;
          const nwr = wr * wr0 - wi * wi0;
          wi = wr * wi0 + wi * wr0;
          wr = nwr;
        }
      }
    }
  }
  window.INSTAR_SPEC = { drawFile, drawBuffer };
})();
