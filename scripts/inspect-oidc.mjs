try {
  const url = process.env.ACTIONS_ID_TOKEN_REQUEST_URL;
  const token = process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
  if (!url || !token) throw new Error("Run only inside a GitHub Actions job with id-token: write.");
  const requestUrl = new URL(url);
  requestUrl.searchParams.set("audience", "api://AzureADTokenExchange");
  const response = await fetch(requestUrl, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(`OIDC token request failed: HTTP ${response.status}`);
  const { value } = await response.json();
  const payload = JSON.parse(Buffer.from(value.split(".")[1], "base64url").toString("utf8"));
  console.log(JSON.stringify({ iss: payload.iss, aud: payload.aud, sub: payload.sub }, null, 2));
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
}
