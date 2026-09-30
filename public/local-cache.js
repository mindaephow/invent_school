// 이 컴퓨터(브라우저)에 저장해 두는 로컬 캐시 — 부품 목록·3D 모델처럼 무겁고 자주 안 바뀌는 자료를 매번 다시 받지 않게 한다.
// IndexedDB(브라우저 안 작은 데이터베이스)에 넣는다. 못 쓰는 환경(시크릿 창 등)에서는 조용히 캐시 없이 동작한다.
//   window.IVS_CACHE.get(key) / set(key, value) / del(key) / clear() / stats()  — 모두 Promise
//   window.IVS_CACHE.hash(text) — 문자열이 바뀌었는지 보는 간단한 지문(저장된 썸네일 등에 사용)
// 원칙: "일단 캐시로 바로 보여주고, 뒤에서 최신을 받아 달라졌으면 갱신"(stale-while-revalidate).
// 지우기: 콘솔에서 IVS_CACHE.clear() (문제가 생겼을 때).
(function () {
  const DB = 'ivs-cache', STORE = 'kv', VERSION = 1;
  let dbp = null;
  function open() {
    if (dbp) return dbp;
    dbp = new Promise((resolve) => {
      try {
        if (!window.indexedDB) return resolve(null);
        const req = indexedDB.open(DB, VERSION);
        req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE); };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => resolve(null);
        req.onblocked = () => resolve(null);
      } catch (e) { resolve(null); }
    });
    return dbp;
  }
  function run(mode, fn) {
    return open().then((db) => new Promise((resolve) => {
      if (!db) return resolve(undefined);
      try {
        const tx = db.transaction(STORE, mode), st = tx.objectStore(STORE);
        const r = fn(st);
        tx.oncomplete = () => resolve(r && 'result' in r ? r.result : undefined);
        tx.onerror = tx.onabort = () => resolve(undefined);
      } catch (e) { resolve(undefined); }
    }));
  }
  // 문자열 지문: 길이 + 일정 간격 글자로 만든 32비트 값 — 썸네일처럼 저장할 때마다 바뀌는 긴 문자열용(충돌 가능성은 매우 낮음)
  function hash(text) {
    const s = String(text == null ? '' : text);
    let h = 5381 ^ s.length;
    const step = Math.max(1, Math.floor(s.length / 4096));
    for (let i = 0; i < s.length; i += step) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
    return s.length + ':' + (h >>> 0).toString(36);
  }
  window.IVS_CACHE = {
    get: (key) => run('readonly', (st) => st.get(key)),
    set: (key, value) => run('readwrite', (st) => st.put(value, key)),
    del: (key) => run('readwrite', (st) => st.delete(key)),
    clear: () => run('readwrite', (st) => st.clear()),
    keys: () => run('readonly', (st) => st.getAllKeys()),
    hash,
    // 저장된 항목 수와 대략의 크기(MB) — 확인용
    async stats() {
      const keys = (await this.keys()) || [];
      let est = null;
      try { if (navigator.storage && navigator.storage.estimate) { const e = await navigator.storage.estimate(); est = Math.round((e.usage || 0) / 1048576 * 10) / 10; } } catch (e) { /* 모르면 생략 */ }
      return { items: keys.length, usedMB: est, keys };
    },
  };
})();
