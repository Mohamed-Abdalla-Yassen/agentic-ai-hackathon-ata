// Tiny cookie helpers. The stack doc calls for the JWT to live in a cookie,
// which the API client then replays as an `Authorization: Bearer` header.
// Readable by JS by design — an httpOnly cookie could not be read back out
// to build that header from the client.

export function getCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`
  const hit = document.cookie
    .split('; ')
    .find((row) => row.startsWith(prefix))
  return hit ? decodeURIComponent(hit.slice(prefix.length)) : null
}

export function setCookie(name, value, { days = 7 } = {}) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  document.cookie =
    `${encodeURIComponent(name)}=${encodeURIComponent(value)}` +
    `; Expires=${expires}; Path=/; SameSite=Lax${secure}`
}

export function deleteCookie(name) {
  document.cookie =
    `${encodeURIComponent(name)}=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/`
}
