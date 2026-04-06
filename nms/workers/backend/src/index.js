const SESSION_COOKIE_NAME = "nms_session";
const MAX_OPERATION_TARGETS = 50;
const SESSION_TTL_SECONDS = 60 * 60 * 24 * 7;
const DEFAULT_LOCAL_ADMIN_EMAIL = "admin@gmail.com";
const DEFAULT_LOCAL_ADMIN_PASSWORD = "admin@gmail.com";
let schemaReady = false;

export default {
  async fetch(request, env) {
    try {
      return await handleRequest(request, env);
    } catch (error) {
      console.error("Unhandled error", error);
      return jsonResponse({ error: "Internal server error." }, 500);
    }
  },
};

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const path = trimTrailingSlash(url.pathname);
  const method = request.method.toUpperCase();

  if (method === "OPTIONS") {
    return withCors(new Response(null, { status: 204 }), request, env);
  }

  await ensureSchema(env);

  if (path === "/" || path === "") {
    return withCors(jsonResponse({ service: "nms-backend-worker", status: "ok" }), request, env);
  }

  if (path === "/api" || path === "/api/") {
    return withCors(jsonResponse({ service: "nms-api", status: "ok" }), request, env);
  }

  if (path === "/api/app-meta" && method === "GET") {
    return withCors(handleAppMeta(env), request, env);
  }

  if (path === "/api/azure-login" && method === "GET") {
    return withCors(handleAzureLogin(env), request, env);
  }

  if (path === "/api/local-login" && method === "POST") {
    return withCors(await handleLocalLogin(request, env), request, env);
  }

  if (path === "/api/session-login" && (method === "POST" || method === "GET")) {
    return withCors(await handleSessionLogin(request, env), request, env);
  }

  if (path === "/api/oauth2/callback" && method === "GET") {
    return withCors(await handleAzureCallback(request, env), request, env);
  }

  if (path === "/api/logout" && method === "POST") {
    return withCors(await handleLogout(request, env), request, env);
  }

  if (path === "/api/active-users" && method === "GET") {
    return withCors(await handleActiveUsers(request, env), request, env);
  }

  if (path === "/api/dashboard" && method === "POST") {
    return withCors(await handleDashboard(request, env), request, env);
  }

  if ((path === "/api/send-email" || path === "/api/dashboard/send-email") && method === "POST") {
    return withCors(await handleSendEmail(request, env), request, env);
  }

  return withCors(jsonResponse({ error: "Not found" }, 404), request, env);
}

function handleAppMeta(env) {
  const contactEmail =
    env.DEFAULT_FROM_EMAIL || env.EMAIL_HOST_USER || env.EMAIL_HOST || "no-reply@example.com";
  return jsonResponse({ contact_email: contactEmail });
}

function handleAzureLogin(env) {
  const tenantId = env.AZURE_TENANT_ID || "";
  const clientId = env.AZURE_CLIENT_ID || "";
  const redirectUri = env.AZURE_REDIRECT_URI || "";
  const scopes = env.AZURE_SCOPES || "openid profile email offline_access User.Read";

  if (!tenantId || !clientId || !redirectUri) {
    return jsonResponse({ error: "Azure SSO is not configured." }, 400);
  }

  const authority = `https://login.microsoftonline.com/${tenantId}`;
  const loginUrl = new URL(`${authority}/oauth2/v2.0/authorize`);
  loginUrl.searchParams.set("client_id", clientId);
  loginUrl.searchParams.set("response_type", "code");
  loginUrl.searchParams.set("redirect_uri", redirectUri);
  loginUrl.searchParams.set("response_mode", "query");
  loginUrl.searchParams.set("scope", scopes);
  loginUrl.searchParams.set("state", crypto.randomUUID());

  return jsonResponse({ login_url: loginUrl.toString() });
}

async function handleLocalLogin(request, env) {
  const payload = await parseJson(request);
  if (!payload) {
    return jsonResponse({ error: "Invalid JSON payload." }, 400);
  }

  const email = String(payload.email || "").trim().toLowerCase();
  const password = String(payload.password || "");
  if (!email || !password) {
    return jsonResponse({ error: "Email and password are required." }, 400);
  }

  await ensureDefaultAdminUser(env);

  const userRow = await env.NMS_DB.prepare(
    `SELECT id, email, username, password_hash, first_name, last_name, role
     FROM users WHERE lower(email) = ?1 OR lower(username) = ?1 LIMIT 1`
  )
    .bind(email)
    .first();

  if (!userRow) {
    return jsonResponse({ error: "Invalid email or password." }, 401);
  }

  const expectedHash = await hashPassword(password, env.AUTH_PASSWORD_SALT || "nms-local-salt");
  if (userRow.password_hash !== expectedHash) {
    return jsonResponse({ error: "Invalid email or password." }, 401);
  }

  const session = await createSession(env, userRow.id, "local");
  await closeOtherActiveLoginActivities(env, userRow.id);
  await env.NMS_DB.prepare(
    `INSERT INTO user_activities (user_id, activity_type, timestamp, session_status, duration)
     VALUES (?1, 'login', ?2, 1, NULL)`
  )
    .bind(userRow.id, isoNow())
    .run();

  const headers = new Headers();
  headers.set("Set-Cookie", buildSessionCookie(session.id, env));

  return jsonResponse(
    {
      access: session.id,
      user: buildUserResponse(userRow),
    },
    200,
    headers
  );
}

async function handleSessionLogin(request, env) {
  const auth = await authenticateRequest(request, env);
  if (!auth.ok) {
    return jsonResponse({ detail: "Authentication credentials were not provided." }, 401);
  }

  return jsonResponse({ user: buildUserResponse(auth.user) });
}

async function handleAzureCallback(request, env) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const nextUrl = url.searchParams.get("next") || "/dashboard";
  if (!code) {
    return jsonResponse({ error: "Missing OAuth code." }, 400);
  }

  const tenantId = env.AZURE_TENANT_ID || "";
  const clientId = env.AZURE_CLIENT_ID || "";
  const clientSecret = env.AZURE_CLIENT_SECRET || "";
  const redirectUri = env.AZURE_REDIRECT_URI || "";
  const scopes = env.AZURE_SCOPES || "openid profile email offline_access User.Read";
  if (!tenantId || !clientId || !clientSecret || !redirectUri) {
    return jsonResponse({ error: "Azure SSO is not configured." }, 400);
  }

  const tokenEndpoint = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/token`;
  const tokenResponse = await fetch(tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      scope: scopes,
      code,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
      client_secret: clientSecret,
    }),
  });

  const tokenData = await safeJson(tokenResponse);
  if (!tokenResponse.ok || !tokenData?.access_token) {
    return jsonResponse({ error: "Token exchange failed", details: tokenData || null }, 400);
  }

  const graphResponse = await fetch("https://graph.microsoft.com/v1.0/me", {
    headers: {
      Authorization: `Bearer ${tokenData.access_token}`,
    },
  });
  const profile = await safeJson(graphResponse);

  const email = String(profile?.mail || profile?.userPrincipalName || "").trim().toLowerCase();
  const displayName = String(profile?.displayName || email || "").trim();
  if (!email) {
    return jsonResponse({ error: "Could not retrieve user email." }, 400);
  }

  const user = await findOrCreateUserFromAzure(env, email, displayName);
  const session = await createSession(env, user.id, "azure");
  await closeOtherActiveLoginActivities(env, user.id);
  await env.NMS_DB.prepare(
    `INSERT INTO user_activities (user_id, activity_type, timestamp, session_status, duration)
     VALUES (?1, 'login', ?2, 1, NULL)`
  )
    .bind(user.id, isoNow())
    .run();

  const frontendUrl = (env.FRONTEND_URL || "http://localhost:3000").replace(/\/$/, "");
  const safeNext = nextUrl.startsWith("/") ? nextUrl : "/dashboard";
  const redirectTarget = `${frontendUrl}${safeNext}`;

  const headers = new Headers({
    Location: redirectTarget,
    "Set-Cookie": buildSessionCookie(session.id, env),
  });

  return new Response(null, { status: 302, headers });
}

async function handleLogout(request, env) {
  const auth = await authenticateRequest(request, env);
  if (!auth.ok) {
    return jsonResponse({ success: false, message: "Not authenticated" }, 401);
  }

  const nowIso = isoNow();
  const nowEpoch = Date.now() / 1000;

  const latestOpenLogin = await env.NMS_DB.prepare(
    `SELECT id, timestamp FROM user_activities
     WHERE user_id = ?1 AND activity_type = 'login' AND session_status = 1
     ORDER BY timestamp DESC LIMIT 1`
  )
    .bind(auth.user.id)
    .first();

  if (latestOpenLogin?.id) {
    const durationSeconds = Math.max(0, nowEpoch - Date.parse(latestOpenLogin.timestamp) / 1000);
    await env.NMS_DB.prepare(
      `UPDATE user_activities
       SET session_status = 0, duration = ?1
       WHERE id = ?2`
    )
      .bind(durationSeconds, latestOpenLogin.id)
      .run();
  }

  await env.NMS_DB.prepare(
    `INSERT INTO user_activities (user_id, activity_type, timestamp, session_status, duration)
     VALUES (?1, 'logout', ?2, 0, 0)`
  )
    .bind(auth.user.id, nowIso)
    .run();

  if (auth.sessionId) {
    await env.NMS_DB.prepare(`DELETE FROM sessions WHERE id = ?1`).bind(auth.sessionId).run();
  }

  const logoutProvider = auth.session?.auth_provider || "";
  const tenantId = env.AZURE_TENANT_ID || "";
  const clientId = env.AZURE_CLIENT_ID || "";
  const postLogout = env.POST_LOGOUT_REDIRECT_URI || env.FRONTEND_URL || "";

  let logoutUrl = "";
  if (logoutProvider === "azure" && tenantId && clientId) {
    const msLogout = new URL(`https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/logout`);
    msLogout.searchParams.set("client_id", clientId);
    if (postLogout) {
      msLogout.searchParams.set("post_logout_redirect_uri", postLogout);
    }
    logoutUrl = msLogout.toString();
  }

  const headers = new Headers();
  headers.set("Set-Cookie", buildExpiredSessionCookie());

  return jsonResponse(
    {
      success: true,
      logout_url: logoutUrl,
      redirect_url: env.FRONTEND_URL || "http://localhost:3000",
    },
    200,
    headers
  );
}

async function handleActiveUsers(request, env) {
  const auth = await authenticateRequest(request, env);
  if (!auth.ok) {
    return jsonResponse({ detail: "Authentication credentials were not provided." }, 401);
  }

  const recentThreshold = new Date(Date.now() - 15 * 60 * 1000).toISOString();

  const activeUsers = await env.NMS_DB.prepare(
    `SELECT DISTINCT u.id, u.email, u.first_name, u.role
     FROM user_activities ua
     JOIN users u ON u.id = ua.user_id
     WHERE ua.timestamp >= ?1 AND ua.activity_type = 'login' AND ua.session_status = 1
     ORDER BY u.id DESC`
  )
    .bind(recentThreshold)
    .all();

  const logs = await env.NMS_DB.prepare(
    `SELECT ua.user_id, u.email, ua.activity_type, ua.timestamp, ua.duration, ua.session_status
     FROM user_activities ua
     JOIN users u ON u.id = ua.user_id
     ORDER BY ua.timestamp DESC
     LIMIT 100`
  ).all();

  const activeRows = activeUsers.results || [];
  const logRows = logs.results || [];

  return jsonResponse({
    active_user_count: activeRows.length,
    active_users: activeRows.map((row) => ({
      id: row.id,
      email: row.email,
      name: row.first_name,
      role: row.role,
    })),
    user_activities: logRows.map((row) => ({
      user_id: row.user_id,
      email: row.email,
      activity_type: row.activity_type,
      timestamp: row.timestamp,
      duration: formatDuration(row.duration),
      session_status: row.session_status ? "Active" : "Closed",
    })),
  });
}

async function handleDashboard(request, env) {
  const auth = await authenticateRequest(request, env);
  if (!auth.ok) {
    return jsonResponse({ error: "Authentication required." }, 401);
  }

  const formData = await request.formData();
  const startIp = String(formData.get("start_ip_address") || "");
  const targets = startIp
    .split(/[\s,]+/)
    .map((value) => value.trim())
    .filter(Boolean);

  if (!targets.length) {
    return jsonResponse({ success: false, error: "No valid IP address or hostname found." }, 400);
  }
  if (targets.length > MAX_OPERATION_TARGETS) {
    return jsonResponse(
      {
        success: false,
        error: `Please enter maximum ${MAX_OPERATION_TARGETS} ip addresses for the operation.`,
      },
      400
    );
  }

  const executorBaseUrl = String(env.DIAGNOSTICS_EXECUTOR_URL || "").trim();
  const executorToken = String(env.DIAGNOSTICS_EXECUTOR_TOKEN || "").trim();
  if (executorBaseUrl) {
    if (!executorToken) {
      return jsonResponse(
        { success: false, error: "Diagnostics executor token is not configured." },
        500
      );
    }

    try {
      const endpoint = `${executorBaseUrl.replace(/\/$/, "")}/dashboard/executor-dashboard/`;
      const proxyResponse = await fetch(endpoint, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${executorToken}`,
        },
        body: formData,
      });

      const proxyData = await safeJson(proxyResponse);
      if (!proxyResponse.ok) {
        return jsonResponse(
          {
            success: false,
            error: proxyData?.error || proxyData?.message || "Diagnostics executor request failed.",
          },
          proxyResponse.status
        );
      }
      return jsonResponse(proxyData || { success: false, error: "Invalid executor response." });
    } catch (error) {
      return jsonResponse(
        {
          success: false,
          error: `Unable to reach diagnostics executor: ${String(error?.message || error)}`,
        },
        502
      );
    }
  }

  const selectedOperations = [
    "enable_ping",
    "verbose_ping",
    "traceroute",
    "dns_lookup",
    "verbos_dns_lookup",
    "simple_snmp_walk",
    "mtr",
    "snmp_walk",
  ].filter((operation) => formData.has(operation));

  const results = selectedOperations.map((operation) => ({
    operation,
    result:
      "Cloudflare Worker runtime cannot execute host OS-level diagnostics directly. Route diagnostics to an external execution service to preserve this operation.",
  }));

  if (!results.length) {
    results.push({
      operation: "none",
      result: "No operations selected.",
    });
  }

  return jsonResponse({ success: true, results });
}

async function handleSendEmail(request, env) {
  const auth = await authenticateRequest(request, env);
  if (!auth.ok) {
    return jsonResponse({ success: false, message: "Authentication required." }, 401);
  }

  const payload = await parseJson(request);
  if (!payload) {
    return jsonResponse({ success: false, message: "Invalid JSON payload" }, 400);
  }

  const emailList = Array.isArray(payload.email_list) ? payload.email_list : [];
  const emailBody = String(payload.email_body || "");
  const emailHtml = String(payload.email_html || "");

  if (!emailList.length || (!emailBody.trim() && !emailHtml.trim())) {
    return jsonResponse({ success: false, message: "Invalid input" }, 400);
  }

  return jsonResponse({
    success: false,
    message:
      "SMTP send is not available in Workers by default. Configure EMAIL_SERVICE_NOTE and route email through an external API.",
  });
}

async function authenticateRequest(request, env) {
  const authHeader = request.headers.get("Authorization") || "";
  if (authHeader.startsWith("Bearer ")) {
    const token = authHeader.slice(7).trim();
    if (token) {
      const session = await getSession(env, token);
      if (session) {
        const user = await findUserById(env, session.user_id);
        if (user) {
          return { ok: true, user, session, sessionId: token };
        }
      }
    }
  }

  const cookies = parseCookieHeader(request.headers.get("Cookie") || "");
  const sessionId = cookies[SESSION_COOKIE_NAME];
  if (!sessionId) {
    return { ok: false };
  }

  const session = await getSession(env, sessionId);
  if (!session) {
    return { ok: false };
  }

  const user = await findUserById(env, session.user_id);
  if (!user) {
    return { ok: false };
  }

  return { ok: true, user, session, sessionId };
}

async function getSession(env, sessionId) {
  const row = await env.NMS_DB.prepare(
    `SELECT id, user_id, auth_provider, expires_at FROM sessions WHERE id = ?1 LIMIT 1`
  )
    .bind(sessionId)
    .first();

  if (!row) {
    return null;
  }

  const expiresAt = Date.parse(row.expires_at);
  if (Number.isFinite(expiresAt) && expiresAt < Date.now()) {
    await env.NMS_DB.prepare(`DELETE FROM sessions WHERE id = ?1`).bind(sessionId).run();
    return null;
  }

  return row;
}

async function createSession(env, userId, provider) {
  const id = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + SESSION_TTL_SECONDS * 1000).toISOString();
  await env.NMS_DB.prepare(
    `INSERT INTO sessions (id, user_id, auth_provider, created_at, expires_at)
     VALUES (?1, ?2, ?3, ?4, ?5)`
  )
    .bind(id, userId, provider, isoNow(), expiresAt)
    .run();

  return { id, user_id: userId, auth_provider: provider, expires_at: expiresAt };
}

async function ensureDefaultAdminUser(env) {
  const adminEmail = (env.DEFAULT_LOCAL_ADMIN_EMAIL || DEFAULT_LOCAL_ADMIN_EMAIL).toLowerCase();
  const adminPassword = env.DEFAULT_LOCAL_ADMIN_PASSWORD || DEFAULT_LOCAL_ADMIN_PASSWORD;
  const passwordHash = await hashPassword(adminPassword, env.AUTH_PASSWORD_SALT || "nms-local-salt");

  const existing = await env.NMS_DB.prepare(`SELECT id FROM users WHERE lower(email) = ?1 LIMIT 1`)
    .bind(adminEmail)
    .first();

  if (!existing) {
    await env.NMS_DB.prepare(
      `INSERT INTO users (
          email, username, password_hash, first_name, last_name, role,
          auth_provider, is_staff, is_superuser, created_at, updated_at
       ) VALUES (?1, ?2, ?3, '', '', 'system_admin', 'local', 1, 1, ?4, ?4)`
    )
      .bind(adminEmail, adminEmail, passwordHash, isoNow())
      .run();
    return;
  }

  await env.NMS_DB.prepare(
    `UPDATE users
     SET username = ?1,
         password_hash = ?2,
         role = 'system_admin',
         is_staff = 1,
         is_superuser = 1,
         updated_at = ?3
     WHERE id = ?4`
  )
    .bind(adminEmail, passwordHash, isoNow(), existing.id)
    .run();
}

async function findOrCreateUserFromAzure(env, email, displayName) {
  const parts = displayName.split(" ").filter(Boolean);
  const firstName = parts[0] || "";
  const lastName = parts.slice(1).join(" ");

  const existing = await env.NMS_DB.prepare(
    `SELECT id, email, username, first_name, last_name, role FROM users WHERE lower(email) = ?1 LIMIT 1`
  )
    .bind(email.toLowerCase())
    .first();

  if (existing) {
    return existing;
  }

  await env.NMS_DB.prepare(
    `INSERT INTO users (
      email, username, password_hash, first_name, last_name, role,
      auth_provider, is_staff, is_superuser, created_at, updated_at
    ) VALUES (?1, ?2, '', ?3, ?4, 'user', 'azure', 0, 0, ?5, ?5)`
  )
    .bind(email.toLowerCase(), email.toLowerCase(), firstName, lastName, isoNow())
    .run();

  return await env.NMS_DB.prepare(
    `SELECT id, email, username, first_name, last_name, role FROM users WHERE lower(email) = ?1 LIMIT 1`
  )
    .bind(email.toLowerCase())
    .first();
}

async function findUserById(env, userId) {
  return env.NMS_DB.prepare(
    `SELECT id, email, username, first_name, last_name, role
     FROM users WHERE id = ?1 LIMIT 1`
  )
    .bind(userId)
    .first();
}

async function closeOtherActiveLoginActivities(env, userId) {
  const openRows = await env.NMS_DB.prepare(
    `SELECT id, timestamp FROM user_activities
     WHERE user_id = ?1 AND activity_type = 'login' AND session_status = 1
     ORDER BY timestamp DESC`
  )
    .bind(userId)
    .all();

  const nowEpoch = Date.now() / 1000;
  for (const row of openRows.results || []) {
    const duration = Math.max(0, nowEpoch - Date.parse(row.timestamp) / 1000);
    await env.NMS_DB.prepare(
      `UPDATE user_activities
       SET session_status = 0, duration = ?1
       WHERE id = ?2`
    )
      .bind(duration, row.id)
      .run();
  }
}

async function ensureSchema(env) {
  if (schemaReady) {
    return;
  }

  await env.NMS_DB.prepare(
    `CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL UNIQUE,
      username TEXT NOT NULL,
      password_hash TEXT NOT NULL DEFAULT '',
      first_name TEXT NOT NULL DEFAULT '',
      last_name TEXT NOT NULL DEFAULT '',
      role TEXT NOT NULL DEFAULT 'user',
      auth_provider TEXT NOT NULL DEFAULT 'local',
      is_staff INTEGER NOT NULL DEFAULT 0,
      is_superuser INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )`
  ).run();

  await env.NMS_DB.prepare(
    `CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      user_id INTEGER NOT NULL,
      auth_provider TEXT NOT NULL DEFAULT 'local',
      created_at TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )`
  ).run();

  await env.NMS_DB.prepare(
    `CREATE TABLE IF NOT EXISTS user_activities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      activity_type TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      session_status INTEGER NOT NULL DEFAULT 1,
      duration REAL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )`
  ).run();

  await env.NMS_DB.prepare(
    `CREATE INDEX IF NOT EXISTS idx_user_activities_user_timestamp
     ON user_activities(user_id, timestamp DESC)`
  ).run();

  schemaReady = true;
}

function buildUserResponse(user) {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    first_name: user.first_name || "",
    last_name: user.last_name || "",
    role: user.role || "user",
  };
}

function buildSessionCookie(sessionId, env) {
  const secure = String(env.COOKIE_SECURE || "true").toLowerCase() === "true";
  const attrs = [
    `${SESSION_COOKIE_NAME}=${encodeURIComponent(sessionId)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${SESSION_TTL_SECONDS}`,
  ];
  if (secure) {
    attrs.push("Secure");
  }
  return attrs.join("; ");
}

function buildExpiredSessionCookie() {
  return `${SESSION_COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`;
}

function parseCookieHeader(value) {
  const cookieMap = {};
  const parts = value.split(";");
  for (const part of parts) {
    const [rawKey, ...rest] = part.trim().split("=");
    if (!rawKey) continue;
    cookieMap[rawKey] = decodeURIComponent(rest.join("=") || "");
  }
  return cookieMap;
}

async function parseJson(request) {
  try {
    return await request.json();
  } catch (_error) {
    return null;
  }
}

async function hashPassword(password, salt) {
  const buffer = new TextEncoder().encode(`${salt}:${password}`);
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return bytesToHex(new Uint8Array(digest));
}

function bytesToHex(bytes) {
  let out = "";
  for (const byte of bytes) {
    out += byte.toString(16).padStart(2, "0");
  }
  return out;
}

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) {
    return "N/A";
  }
  const total = Math.max(0, Math.floor(Number(seconds)));
  const h = String(Math.floor(total / 3600)).padStart(2, "0");
  const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function trimTrailingSlash(path) {
  if (path === "/") {
    return "/";
  }
  return path.endsWith("/") ? path.slice(0, -1) : path;
}

function isoNow() {
  return new Date().toISOString();
}

function jsonResponse(payload, status = 200, extraHeaders = new Headers()) {
  const headers = new Headers(extraHeaders);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json; charset=utf-8");
  }
  return new Response(JSON.stringify(payload), { status, headers });
}

function withCors(response, request, env) {
  const headers = new Headers(response.headers);
  const reqOrigin = request.headers.get("Origin");
  const allowed = String(env.CORS_ALLOWED_ORIGINS || "").split(",").map((v) => v.trim()).filter(Boolean);

  if (reqOrigin && (allowed.includes("*") || allowed.includes(reqOrigin))) {
    headers.set("Access-Control-Allow-Origin", reqOrigin);
  } else if (allowed.length && allowed[0] !== "*") {
    headers.set("Access-Control-Allow-Origin", allowed[0]);
  }

  headers.set("Access-Control-Allow-Credentials", "true");
  headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRFToken");
  headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  headers.set("Vary", "Origin");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch (_error) {
    return null;
  }
}
