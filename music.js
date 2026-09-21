document.addEventListener('click', function (e) {
  var btn = e.target.closest('.tt');
  if (!btn) return;
  e.preventDefault();
  var li = btn.closest('li');
  var existing = li.querySelector('.track-embed');
  if (existing) {
    existing.remove();
    btn.classList.remove('playing');
    return;
  }
  document.querySelectorAll('.track-embed').forEach(function (el) { el.remove(); });
  document.querySelectorAll('.tt.playing').forEach(function (el) { el.classList.remove('playing'); });
  var id = btn.getAttribute('data-track-id');
  var wrap = document.createElement('div');
  wrap.className = 'track-embed';
  var iframe = document.createElement('iframe');
  iframe.src = 'https://open.spotify.com/embed/track/' + id + '?utm_source=oembed';
  iframe.width = '100%';
  iframe.height = '152';
  iframe.frameBorder = '0';
  iframe.allow = 'autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture';
  iframe.loading = 'lazy';
  wrap.appendChild(iframe);
  li.appendChild(wrap);
  btn.classList.add('playing');
});
