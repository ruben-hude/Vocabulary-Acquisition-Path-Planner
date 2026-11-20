(() => {
  // ---------- Adresses de l'API (à vérifier dans /docs) ----------
  const API = {
    profile: "/api/profile",
    readBooks: "/api/read-books",
    currentPath: "/api/current-path",
    preferences: "/api/preferences",
  };

  // ---------- Traductions : l'API envoie de l'anglais, la page est en français ----------
  const MONTHS_SHORT = {
    January: "Janv.", February: "Févr.", March: "Mars", April: "Avr.", May: "Mai", June: "Juin",
    July: "Juil.", August: "Août", September: "Sept.", October: "Oct.", November: "Nov.", December: "Déc.",
  };
  const MONTHS_LONG = {
    January: "janvier", February: "février", March: "mars", April: "avril", May: "mai", June: "juin",
    July: "juillet", August: "août", September: "septembre", October: "octobre", November: "novembre", December: "décembre",
  };
  const PATH_TYPES = { progressive: "progressif", shortest: "le plus court", gentlest: "le plus doux" };
  const GENRES = { Classics: "Classique", "Science fiction": "Science-fiction", Crime: "Policier", Biography: "Biographie" };
  const STEP_CLASS = { read: "done", in_progress: "current", upcoming: "", target: "cible" };
  const STEP_LABEL = { read: "Lu", in_progress: "En cours", upcoming: "À venir" };
  const CHECK_SVG = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3.5 8.3l3 3 6-6.6" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  // ---------- Outils ----------
  const fmt = n => n.toLocaleString("fr-FR");
  const dateFR = iso => new Date(iso + "T12:00:00")
    .toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
  const memberSinceFR = text => {            // "June 2026" → "juin 2026"
    const [month, year] = text.split(" ");
    return `${MONTHS_LONG[month] ?? month} ${year ?? ""}`.trim();
  };

  function el(tag, className, text) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (text !== undefined) e.textContent = text;   // textContent : pas d'injection de HTML
    return e;
  }

  async function getJSON(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url} → erreur ${response.status}`);
    return response.json();
  }

  function showError(message) {
    const banner = el("div", "", message);
    banner.style.cssText = "position:fixed;top:0;left:0;right:0;padding:10px;background:#d65a5a;color:#fff;text-align:center;font-weight:500;z-index:10";
    document.body.prepend(banner);
  }

  // ---------- Profil : identité, niveau, pastille ----------
  function renderProfile(p, targetTitle) {
    document.querySelector("#profil .user-name").textContent = p.name;
    document.querySelector("#profil .avatar").textContent = p.name.trim().charAt(0).toUpperCase();
    document.querySelector("#profil .user-info").textContent =
      `Membre depuis ${memberSinceFR(p.member_since)}  ·  ${p.nb_read_books} livres lus`;
    document.querySelector(".niveau-badge").textContent = p.level;
    document.querySelector(".niveau strong").textContent = `${fmt(p.known_words)} mots connus`;
    document.querySelectorAll(".chip-vocab").forEach(c => {
      c.textContent = `Niveau ${p.level}  ·  ${fmt(p.known_words)} mots connus  ·  Objectif : ${targetTitle}`;
    });
    document.querySelector("#parcours .depart small").textContent = `${fmt(p.known_words)} mots`;
    document.querySelector("#parcours .depart em").textContent = p.level;
    renderCurve(p.history);
  }

  // ---------- Courbe du vocabulaire ----------
  function renderCurve(history) {
    if (!history.length) return;
    const MIN = 1000, MAX = 5000;      // valeurs de l'axe vertical
    const TOP = 12, BOTTOM = 222;      // positions en pixels de 5 000 et de 1 000
    const X0 = 124, X1 = 1104;         // premier et dernier point
    const n = history.length;
    const x = i => (n === 1 ? X1 : X0 + (i * (X1 - X0)) / (n - 1));
    const y = v => BOTTOM - ((Math.min(Math.max(v, MIN), MAX) - MIN) * (BOTTOM - TOP)) / (MAX - MIN);
    const points = history.map((h, i) => [x(i), y(h.known_words)]);
    const last = points[n - 1];

    document.querySelector("#curve-line").setAttribute("points", points.map(p => p.join(",")).join(" "));
    document.querySelector("#curve-area").setAttribute("d",
      "M" + points.map(p => p.join(" ")).join(" L") + ` L${last[0]} ${BOTTOM} L${points[0][0]} ${BOTTOM} Z`);

    const NS = "http://www.w3.org/2000/svg";
    document.querySelector("#curve-points").replaceChildren(...points.slice(0, -1).map(([cx, cy]) => {
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", 5);
      return c;
    }));
    const dot = document.querySelector("#curve-last");
    dot.setAttribute("cx", last[0]); dot.setAttribute("cy", last[1]);

    // Étiquettes : on supprime les anciennes et on recrée
    const curve = document.querySelector(".courbe");
    curve.querySelectorAll(".mois, .val-depart, .tooltip").forEach(e => e.remove());
    history.forEach((h, i) => {
      const m = el("span", "mois", MONTHS_SHORT[h.month] ?? h.month);
      m.style.left = x(i) + "px";
      curve.appendChild(m);
    });
    const first = el("span", "val-depart", fmt(history[0].known_words));
    first.style.cssText = `left:${points[0][0]}px;top:${points[0][1] - 28}px;transform:translateX(-50%)`;
    const bubble = el("span", "tooltip", `${fmt(history[n - 1].known_words)} mots`);
    bubble.style.cssText = `left:${last[0]}px;top:${last[1] - 44}px;transform:translateX(-50%)`;
    curve.append(first, bubble);
  }

  // ---------- Derniers livres lus ----------
  function renderReadBooks(books) {
    document.querySelector(".livres").replaceChildren(...books.slice(0, 3).map(b => {
      const card = el("article", "livre");
      const img = el("img");
      img.src = b.cover_url;
      img.alt = `Couverture de ${b.title}`;
      img.onerror = () => { img.style.visibility = "hidden"; };   // image introuvable : on masque
      const info = el("div", "livre-infos");
      info.append(
        el("h3", "", b.title),
        el("div", "auteur muted", `${b.author}  ·  ${b.level}`),
        el("div", "date muted", `Terminé le ${dateFR(b.completed_at)}`),
        el("span", "pill", `+ ${fmt(b.learned_words)} mots appris`)
      );
      card.append(img, info);
      return card;
    }));
  }

  // ---------- Chemin en cours ----------
  function renderPath(path) {
    const card = document.querySelector("#profil .chemin");
    const beforeTarget = path.steps.filter(s => s.status !== "target");
    const done = beforeTarget.filter(s => s.status === "read").length;

    card.querySelector("h2").textContent = `Vers ${path.target_title}`;
    card.querySelector(".meta").textContent =
      `Chemin ${PATH_TYPES[path.path_type] ?? path.path_type}  ·  ${beforeTarget.length} livres avant la cible`;
    card.querySelector(".prog-labels span:last-child").textContent = `${done} / ${beforeTarget.length} livres`;
    card.querySelector(".barre > div").style.width =
      (beforeTarget.length ? (100 * done) / beforeTarget.length : 0) + "%";

    card.querySelector(".etapes").replaceChildren(...path.steps.map((s, i) => {
      const row = el("div", ("etape " + (STEP_CLASS[s.status] ?? "")).trim());
      const marker = el("div", "repere");
      if (s.status === "read") marker.innerHTML = CHECK_SVG;   // constante, pas une donnée de l'API
      else marker.textContent = String(i + 1);
      const text = el("div", "etape-texte");
      text.append(
        el("strong", "", s.title),
        el("span", "", `${s.author}  ·  ${s.level}  ·  + ${fmt(s.new_words)} mots`)
      );
      const end = s.status === "target"
        ? el("span", "tag-cible", "Livre cible")
        : el("span", "statut", STEP_LABEL[s.status] ?? s.status);
      row.append(marker, text, end);
      return row;
    }));
  }

  // ---------- Préférences ----------
  function renderPreferences(p) {
    const shown = p.genres.slice(0, 4);
    const rest = p.genres.length - shown.length;
    const genres = document.querySelector(".prefs .genres");
    genres.replaceChildren(...shown.map(g => el("span", "pill", GENRES[g] ?? g)));
    if (rest > 0) genres.append(el("span", "pill more", `+ ${rest}`));
    const n = p.favorite_books.length;
    document.querySelector("#liked-count").textContent = `${n} livre${n > 1 ? "s" : ""} aimé${n > 1 ? "s" : ""}`;
  }

  // ---------- Lancement ----------
  async function init() {
    try {
      const [profile, books, path, preferences] = await Promise.all([
        getJSON(API.profile),
        getJSON(API.readBooks),
        getJSON(API.currentPath),
        getJSON(API.preferences),
      ]);
      renderProfile(profile, path.target_title);
      renderReadBooks(books);
      renderPath(path);
      renderPreferences(preferences);
    } catch (error) {
      console.error(error);
      showError("Impossible de charger les données : l'API est-elle lancée ?");
    }
  }
  init();
})();