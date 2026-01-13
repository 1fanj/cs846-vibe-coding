const API_BASE = window.location.origin;

function el(id){return document.getElementById(id)}

function saveToken(t){localStorage.setItem('vibe_token', t)}
function getToken(){return localStorage.getItem('vibe_token')}
function clearToken(){localStorage.removeItem('vibe_token')}

async function api(path, opts={}){
  const headers = opts.headers || {};
  const token = getToken();
  if(token) headers['Authorization'] = `Bearer ${token}`;
  if(opts.json){
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.json);
    delete opts.json;
  }
  const res = await fetch(API_BASE + path, {...opts, headers});
  const text = await res.text();
  try{ return JSON.parse(text);}catch(e){ return text }
}

async function register(){
  const username = el('reg_username').value.trim();
  const display_name = el('reg_display').value.trim();
  const password = el('reg_password').value;
  const r = await api('/register', {method:'POST', json:{username, display_name, password}});
  if(r && r.access_token){ saveToken(r.access_token); showMe(username); }
  else alert(JSON.stringify(r));
}

async function login(){
  const username = el('login_username').value.trim();
  const password = el('login_password').value;
  // OAuth2 token endpoint expects form data
  const fd = new FormData(); fd.append('username', username); fd.append('password', password);
  const res = await fetch(API_BASE + '/token', {method:'POST', body: fd});
  const data = await res.json();
  if(data && data.access_token){ saveToken(data.access_token); showMe(username); }
  else alert(JSON.stringify(data));
}

function showMe(username){
  el('me_user').textContent = username;
  el('me').style.display = 'block';
}

function logout(){ clearToken(); el('me').style.display='none'; }

async function createPost(){
  const content = el('post_content').value.trim();
  if(!content) return alert('Empty post');
  const r = await api('/posts', {method:'POST', json:{content}});
  if(r && r.id){ el('post_content').value = ''; await refreshFeed(); }
  else alert(JSON.stringify(r));
}

function makePostNode(p){
  const d = document.createElement('div'); d.className='post';
  d.innerHTML = `<div class="meta">#${p.id} by ${p.author_id} at ${p.created_at}</div><div class="content">${escapeHtml(p.content)}</div><div class="actions"><button data-id="${p.id}" class="like">Like (${p.likes})</button></div>`;
  d.querySelector('.like').addEventListener('click', async e=>{
    const id = e.target.dataset.id; const res = await api(`/posts/${id}/like`, {method:'POST'});
    if(res && res.status==='ok') refreshFeed(); else alert(JSON.stringify(res));
  });
  return d;
}

function escapeHtml(s){return s.replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c]));}

async function refreshFeed(){
  const feed = await api('/feed');
  const container = el('posts'); container.innerHTML='';
  if(Array.isArray(feed)){
    feed.forEach(p=> container.appendChild(makePostNode(p)));
  } else { container.textContent = JSON.stringify(feed); }
}

el('btn_register').addEventListener('click', register);
el('btn_login').addEventListener('click', login);
el('btn_logout').addEventListener('click', logout);
el('btn_post').addEventListener('click', createPost);
el('btn_refresh').addEventListener('click', refreshFeed);

// initial load
if(getToken()){ el('me').style.display='block'; }
refreshFeed();
