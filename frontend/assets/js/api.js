const API_BASE = '/api';

export function getToken(){
  return localStorage.getItem('tbmonitoring_token') || '';
}

export function setToken(token){
  localStorage.setItem('tbmonitoring_token', token);
}

export function clearToken(){
  localStorage.removeItem('tbmonitoring_token');
}

function base64UrlDecode(str){
  const b64 = str.replace(/-/g, '+').replace(/_/g, '/');
  const pad = '='.repeat((4 - (b64.length % 4)) % 4);
  return atob(b64 + pad);
}

export function decodeJwtPayload(token){
  if(!token) return null;
  const parts = token.split('.');
  if(parts.length !== 3) return null;
  try{
    const payloadStr = base64UrlDecode(parts[1]);
    return JSON.parse(payloadStr);
  }catch{
    return null;
  }
}

export function getUserRole(){
  const t = getToken();
  const payload = decodeJwtPayload(t);
  return payload?.role || null;
}

export function requireRole(expectedRole){
  const role = getUserRole();
  if(!role) return false;
  if(expectedRole && role !== expectedRole) return false;
  return true;
}


export async function apiFetch(path, {method='GET', body=null, headers={}, token=true}={}){
  const finalHeaders = { 'Content-Type': 'application/json', ...headers };
  if(token){
    const t = getToken();
    if(t) finalHeaders['Authorization'] = `Bearer ${t}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: finalHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const ct = res.headers.get('content-type') || '';
  if(ct.includes('application/json')) data = await res.json().catch(()=>null);
  else data = await res.text().catch(()=>null);

  if(!res.ok){
    const msg = (data && data.detail) ? data.detail : (typeof data==='string' ? data : `HTTP ${res.status}`);
    throw new Error(msg);
  }
  return data;
}


export function showToast(message, type='info', duration=4000){
  let container = document.querySelector('.toast-container');
  if(!container){
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(()=>{
    el.style.animation = 'toastOut .3s ease forwards';
    setTimeout(()=>el.remove(), 300);
  }, duration);
}

export function renderLoadingRow(colspan, message='Loading...'){
  return `<tr><td colspan="${colspan}" class="loading-row"><div class="spinner"></div>${message}</td></tr>`;
}

export function renderSpinner(message='Loading...'){
  return `<div style="text-align:center;padding:24px;"><div class="spinner spinner-lg"></div><div class="muted">${message}</div></div>`;
}

export async function wsConnect(onMessage){
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}${API_BASE}/ws/chat`);
  ws.onmessage = (e)=>{
    try{
      onMessage(JSON.parse(e.data));
    }catch{
      onMessage(e.data);
    }
  };
  return ws;
}

export function wsConnectAlerts(onAlert){
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}${API_BASE}/ws/alerts`);
  ws.onmessage = (e)=>{
    try{
      const data = JSON.parse(e.data);
      if(data.type === 'new_alert') onAlert(data.alert);
    }catch{ /* ignore */ }
  };
  ws.onclose = ()=>{
    setTimeout(()=>wsConnectAlerts(onAlert), 3000);
  };
  return ws;
}

