/* Toy RSA for classroom primes. Not for secrets. */
(function () {
  function modexp(b, e, m) {
    b = BigInt(b);
    e = BigInt(e);
    m = BigInt(m);
    let r = 1n;
    b %= m;
    while (e > 0n) {
      if (e & 1n) r = (r * b) % m;
      b = (b * b) % m;
      e >>= 1n;
    }
    return Number(r);
  }
  function factor(n) {
    n = Number(n);
    // Classroom RSA needs two integers >= 2. Reject 0/1/2/primes-and-junk early
    // so the workbench never prints q=1 (or q=0) from n%2===0.
    if (!Number.isFinite(n) || !Number.isInteger(n) || n < 4) return null;
    if (n % 2 === 0) return [2, n / 2];
    const lim = Math.floor(Math.sqrt(n));
    for (let p = 3; p <= lim; p += 2) {
      if (n % p === 0) return [p, n / p];
    }
    return null;
  }
  function egcd(a, b) {
    if (a === 0n) return [b, 0n, 1n];
    const [g, y, x] = egcd(b % a, a);
    return [g, x - (b / a) * y, y];
  }
  function modinv(a, m) {
    const [g, x] = egcd(BigInt(a), BigInt(m));
    if (g !== 1n) return null;
    return Number(((x % BigInt(m)) + BigInt(m)) % BigInt(m));
  }
  function decryptBlock(c, d, n) {
    // Classroom workbench: refuse null/non-finite d (e not coprime to phi)
    // so BigInt(null) never throws mid-decrypt.
    if (d == null || n == null || !Number.isFinite(Number(d)) || !Number.isFinite(Number(n))) {
      return null;
    }
    return modexp(c, d, n);
  }
  window.INSTAR_RSA = { modexp, factor, modinv, decryptBlock };
})();
