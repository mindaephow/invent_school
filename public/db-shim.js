// Firestore-style db.collection(...).where(...).get()/.add()/.doc(id).update()/.delete()
// backed by Supabase Postgres. Each "collection" is a table with (id uuid, data jsonb, ...).
// Mirrors the Claude Artifact `db` capability's API shape so the app code written against
// that API doesn't need to change. Access control lives in the database (RLS), not here.
//
// Sessions are kept in sessionStorage (cleared when the tab/browser closes) so a shared
// tablet never stays logged in as the previous person. Teacher and student pages use
// different storageKeys so one role's login never leaks into the other's.
function createSupabaseDb(supabaseUrl, supabaseKey, options) {
  options = options || {};
  let storage;
  try { storage = window.sessionStorage; storage.getItem('x'); }
  catch (e) {
    const mem = {};
    storage = { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); }, removeItem: k => { delete mem[k]; } };
  }
  const client = window.supabase.createClient(supabaseUrl, supabaseKey, {
    auth: {
      storage,
      storageKey: options.storageKey || 'ivs-auth',
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: options.detectSessionInUrl === true
    }
  });

  const TABLES = {
    teachers: 'ivs_teachers',
    courses: 'ivs_courses',
    students: 'ivs_students',
    records: 'ivs_records',
    curriculum: 'ivs_curriculum',
    projects: 'ivs_projects'
  };

  // row.data is the document; other columns (login_id, user_id, ...) come along as `row`
  function wrapRow(row) {
    return { id: row.id, data: () => row.data || {}, row };
  }

  function collection(name) {
    const table = TABLES[name] || name;
    const filters = [];

    const api = {
      where(field, op, value) {
        filters.push({ field, op, value });
        return api;
      },
      async get() {
        let q = client.from(table).select('*');
        filters.forEach(f => {
          const col = `data->>${f.field}`;
          const val = String(f.value);
          if (f.op === '!=') q = q.neq(col, val);
          else q = q.eq(col, val);
        });
        const { data, error } = await q;
        if (error) { console.error('[db] get failed', table, error); return { empty: true, docs: [], error }; }
        const docs = (data || []).map(wrapRow);
        return { empty: docs.length === 0, docs };
      },
      async add(obj) {
        const { data, error } = await client.from(table).insert({ data: obj }).select('id').single();
        if (error) { console.error('[db] add failed', table, error); throw error; }
        return { id: data.id };
      },
      doc(id) {
        return {
          async update(patch) {
            const { data: cur, error: e1 } = await client.from(table).select('data').eq('id', id).single();
            if (e1) { console.error('[db] update-read failed', table, id, e1); throw e1; }
            const merged = Object.assign({}, cur.data || {}, patch);
            const { error } = await client.from(table).update({ data: merged }).eq('id', id);
            if (error) { console.error('[db] update failed', table, id, error); throw error; }
          },
          async delete() {
            const { error } = await client.from(table).delete().eq('id', id);
            if (error) { console.error('[db] delete failed', table, id, error); throw error; }
          }
        };
      }
    };
    return api;
  }

  return {
    collection,
    client,
    auth: client.auth,
    rpc: (fn, args) => client.rpc(fn, args)
  };
}
