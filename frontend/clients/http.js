// ============================================================
//  统一后端请求层（与 OCR-IPMS axios 拦截器同形态，无构建步骤实现）
//  挂在 window.PmHttp。
//  - 注入 Authorization Bearer
//  - 401 时用 refresh_token 续期并重试一次
//  - 自动解包 R1 响应信封 {code,message,data} → 返回 data
//  - 把后端真实 message 作为 Error.message，附 code/status，便于调用方判断
// ============================================================
(function () {
  const unwrapEnvelope = (json) =>
    json && typeof json === 'object' && 'code' in json && 'data' in json
      ? json.data
      : json;

  // 工厂：注入运行时依赖（认证头、refresh、登出回调）
  // opts: { baseUrl, getAuthHeaders, tryRefresh, onUnauthorized }
  const createApi = (opts) => {
    const { baseUrl, getAuthHeaders, tryRefresh, onUnauthorized } = opts;

    const api = async (path, { method = 'GET', body, isForm = false, _retried = false } = {}) => {
      const headers = { ...getAuthHeaders() };
      if (body != null && !isForm) headers['Content-Type'] = 'application/json';
      const payload = isForm ? body : body != null ? JSON.stringify(body) : undefined;

      let res;
      try {
        res = await fetch(`${baseUrl}${path}`, { method, headers, body: payload });
      } catch (e) {
        throw Object.assign(new Error('网络连接失败，请检查后端服务是否可用'), { status: 0 });
      }

      // access_token 失效：尝试续期后重试一次；失败则登出
      if (res.status === 401 && !_retried && !path.includes('/auth/')) {
        if (tryRefresh && (await tryRefresh())) {
          return api(path, { method, body, isForm, _retried: true });
        }
        if (onUnauthorized) onUnauthorized();
        throw Object.assign(new Error('登录状态已过期，请重新登录'), { status: 401 });
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw Object.assign(
          new Error(data.message || data.detail || `请求失败 (${res.status})`),
          { status: res.status, code: data.code },
        );
      }
      if (res.status === 204) return null;
      return unwrapEnvelope(await res.json().catch(() => null));
    };

    return api;
  };

  window.PmHttp = { createApi, unwrapEnvelope };
})();
