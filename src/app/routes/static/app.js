(() => {
  // ---------- Adresses de l'API (à vérifier dans /docs) ----------
  const API = {
    profile: "/api/profile",
    readBooks: "/api/read-books",
    books: "/api/books",
    path: "/api/path",
    preferences: "/api/preferences",
  };

  let booksById = new Map();
  let readBookIds = new Set();
  let selectedTargetBookId = "";
  let selectedReadBookId = "";

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

  // ---------- Outils ----------
  const fmt = n => n.toLocaleString("fr-FR");
  const normalizeBookId = id => {
    const match = /^(?:book_)?(\d+)(?:\.txt)?$/.exec(String(id));
    return match ? match[1] : String(id);
  };
  const normalizeSearchText = text => String(text ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
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

  // Bloc de remplacement quand un livre n'a pas de couverture
  function coverPlaceholder(title) {
    const d = el("div", "", title);
    d.style.cssText = "width:175px;height:260px;border-radius:8px;flex-shrink:0;" +
      "background:linear-gradient(90deg,#d1bdf2,#8c6ecc);color:#fff;font-weight:700;" +
      "font-size:20px;line-height:1.25;display:flex;align-items:center;" +
      "justify-content:center;text-align:center;padding:0 14px";
    return d;
  }

  // Miniatures des « livres aimés » : de simples pastilles, car l'API n'envoie que des identifiants
  function renderMinis(count) {
    const minis = document.querySelector(".minis");
    const n = Math.min(count, 3);
    minis.replaceChildren(...Array.from({ length: n }, (_, i) => {
      const m = el("div");
      m.style.cssText = "width:36px;height:52px;border:2px solid #fff;border-radius:6px;" +
        "background:linear-gradient(90deg,#d1bdf2,#8c6ecc);" +
        `margin-right:${i === n - 1 ? 0 : -10}px`;
      return m;
    }));
  }

  // ---------- Profil : identité, niveau, pastille ----------
  function renderProfile(p, targetTitle) {
    document.querySelector("#profil .user-name").textContent = p.name;
    document.querySelector("#profil .avatar").textContent = p.name.trim().charAt(0).toUpperCase();
    document.querySelector("#profil .user-info").textContent =
      `Membre depuis ${memberSinceFR(p.member_since)}  ·  ${p.nb_read_books} livres lus`;
    document.querySelector(".niveau-badge").textContent = p.level;
    document.querySelector(".niveau .known-words").textContent = `${fmt(p.known_words)} mots connus`;
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
  function enrichReadBooks(books) {
    return books.map(book => {
      const catalogBook = booksById.get(normalizeBookId(book.id));
      return catalogBook
        ? { ...book, title: catalogBook.title, author: catalogBook.author }
        : book;
    });
  }

  function renderReadBooks(books) {
    const enrichedBooks = enrichReadBooks(books);
    document.querySelector(".livres").replaceChildren(...enrichedBooks.slice(0, 3).map(b => {
      const card = el("article", "livre");
      let cover;
      if (b.cover_url) {
        cover = el("img");
        cover.src = b.cover_url;
        cover.alt = `Couverture de ${b.title}`;
        cover.onerror = () => cover.replaceWith(coverPlaceholder(b.title));   // image introuvable
      } else {
        cover = coverPlaceholder(b.title);
      }
      const info = el("div", "livre-infos");
      info.append(
        el("h3", "", b.title),
        el("div", "auteur muted", `${b.author}  ·  ${b.level}`),
        el("div", "date muted", `Terminé le ${dateFR(b.completed_at)}`),
        el("span", "pill", `+ ${fmt(b.learned_words)} mots appris`)
      );
      card.append(cover, info);
      return card;
    }));
  }

  function renderReadHistory(books) {
    const sortedBooks = enrichReadBooks(books).sort((a, b) =>
      b.completed_at.localeCompare(a.completed_at) || a.title.localeCompare(b.title, "fr")
    );
    const list = document.querySelector("#read-history-list");
    const emptyMessage = document.querySelector("#read-history-empty");
    document.querySelector("#read-history-count").textContent =
      `${sortedBooks.length} livre${sortedBooks.length > 1 ? "s" : ""}`;
    emptyMessage.hidden = sortedBooks.length > 0;
    list.replaceChildren(...sortedBooks.map(book => {
      const item = el("article", "read-history-item");
      const info = el("div", "read-history-info");
      info.append(
        el("strong", "", book.title),
        el("span", "", book.author)
      );
      const meta = el("div", "read-history-meta");
      const date = el("time", "read-history-date", `Lu le ${dateFR(book.completed_at)}`);
      date.dateTime = book.completed_at;
      meta.append(date, el("span", "pill", `+ ${fmt(book.learned_words)} mots appris`));
      item.append(info, meta);
      return item;
    }));
  }

  // ---------- Chemin en cours ----------
  function createPathStep(step, index) {
    const row = el("div", ("etape " + (STEP_CLASS[step.status] ?? "")).trim());
    const marker = el("div", "repere", String(index + 1));
    const text = el("div", "etape-texte");
    text.append(
      el("strong", "", step.title),
      el("span", "", `${step.author}  ·  Coût : ${fmt(step.cost)} occurrences`)
    );
    const end = step.status === "target"
      ? el("span", "tag-cible", "Livre cible")
      : el("span", "statut", STEP_LABEL[step.status] ?? step.status);
    row.append(marker, text, end);
    return row;
  }

  function renderPath(path) {
    const card = document.querySelector("#profil .chemin");
    const pathSteps = path?.steps ?? [];
    if (!path) {
      card.querySelector("h2").textContent = "Aucun parcours calculé";
      card.querySelector(".meta").textContent = "Choisis une cible dans la page Parcours.";
      card.querySelector(".prog-labels span:last-child").textContent = "—";
      card.querySelector(".barre > div").style.width = "0%";
      card.querySelector(".etapes").replaceChildren();
      return;
    }

    const beforeTarget = pathSteps.filter(s => s.status !== "target");
    const done = beforeTarget.filter(s => s.status === "read").length;

    card.querySelector("h2").textContent = `Vers ${path.target_title}`;
    card.querySelector(".meta").textContent =
      `Chemin ${PATH_TYPES[path.path_type] ?? path.path_type}  ·  ${beforeTarget.length} livres avant la cible`;
    card.querySelector(".prog-labels span:last-child").textContent = `${done} / ${beforeTarget.length} livres`;
    card.querySelector(".barre > div").style.width =
      (beforeTarget.length ? (100 * done) / beforeTarget.length : 0) + "%";

    card.querySelector(".etapes").replaceChildren(
      ...pathSteps.map(createPathStep)
    );
  }

  function renderWorkflowSteps(steps) {
    document.querySelector("#path-results").replaceChildren(
      ...steps.map(createPathStep)
    );
  }

  function populateBookControls(catalog, readBooks) {
    booksById = new Map(catalog.map(book => [String(book.id), book]));
    readBookIds = new Set(readBooks.map(book => normalizeBookId(book.id)));

    document.querySelector("#target-book-search").disabled = false;
    document.querySelector("#target-book-search-status").textContent =
      "Saisis un titre ou un auteur pour rechercher.";
    document.querySelector("#read-book-search").disabled = false;
    document.querySelector("#read-book-search-status").textContent =
      "Saisis un titre ou un auteur pour rechercher.";
    updateReadBookAction();
  }

  function findBooksMatchingQuery(query) {
    const normalizedQuery = normalizeSearchText(query.trim());
    if (!normalizedQuery) {
      return [];
    }

    return [...booksById.values()]
      .filter(book => normalizeSearchText(`${book.title} ${book.author}`).includes(normalizedQuery))
      .sort((a, b) => a.title.localeCompare(b.title, "fr"));
  }

  function createBookSearchResult(book, onSelect, isRead = null) {
    const item = el("li");
    const button = el("button", "book-search-result");
    button.type = "button";
    const readStatus = isRead === null ? "" : isRead ? "déjà marqué comme lu" : "non lu";
    button.setAttribute("aria-label", `${book.title}, ${book.author}${readStatus ? `, ${readStatus}` : ""}`);

    const copy = el("span", "book-search-result-copy");
    copy.append(el("strong", "", book.title), el("span", "", book.author));
    button.append(copy);
    if (isRead !== null) {
      const state = el("span", `book-search-result-state${isRead ? " is-read" : ""}`, isRead ? "Déjà lu" : "Non lu");
      button.append(state);
    }
    button.addEventListener("click", onSelect);
    item.append(button);
    return item;
  }

  function renderBookSearchResults(query, resultsId, statusId, onSelect, showReadState = false) {
    const normalizedQuery = normalizeSearchText(query.trim());
    const results = document.querySelector(`#${resultsId}`);
    const searchStatus = document.querySelector(`#${statusId}`);
    if (!normalizedQuery) {
      results.replaceChildren();
      results.hidden = true;
      searchStatus.textContent = "Saisis un titre ou un auteur pour rechercher.";
      return;
    }

    const matches = findBooksMatchingQuery(query);
    const visibleMatches = matches.slice(0, 8);
    results.replaceChildren(...visibleMatches.map(book =>
      createBookSearchResult(
        book,
        () => onSelect(book),
        showReadState ? readBookIds.has(normalizeBookId(book.id)) : null
      )
    ));
    results.hidden = visibleMatches.length === 0;

    if (matches.length === 0) {
      searchStatus.textContent = "Aucun livre trouvé. Essaie un autre titre ou auteur.";
    } else if (matches.length > visibleMatches.length) {
      searchStatus.textContent = `${visibleMatches.length} résultats affichés sur ${matches.length}. Affine ta recherche.`;
    } else {
      searchStatus.textContent = `${matches.length} résultat${matches.length > 1 ? "s" : ""}.`;
    }
  }

  function selectTargetBook(book) {
    selectedTargetBookId = String(book.id);
    document.querySelector("#target-book-results").hidden = true;
    document.querySelector("#target-book-search-status").textContent =
      `Livre cible sélectionné : ${book.title} — ${book.author}.`;
    renderPath(null);
    renderWorkflowSteps([]);
    setPathStatus("Clique sur « Calculer le chemin » pour lancer le calcul.");
    document.querySelector("#calculate-path").focus();
  }

  function selectReadBook(book) {
    selectedReadBookId = String(book.id);
    document.querySelector("#read-book-results").hidden = true;
    document.querySelector("#read-book-search-status").textContent =
      `Livre sélectionné : ${book.title} — ${book.author}.`;
    updateReadBookAction();
    document.querySelector("#toggle-read-book").focus();
  }

  function updateReadBookAction() {
    const bookId = selectedReadBookId;
    const button = document.querySelector("#toggle-read-book");
    const status = document.querySelector("#read-state-status");
    status.style.color = "";
    if (!bookId) {
      button.disabled = true;
      button.textContent = "Marquer comme lu";
      status.textContent = "Recherche un livre et sélectionne un résultat.";
      return;
    }

    const isRead = readBookIds.has(bookId);
    const book = booksById.get(bookId);
    button.disabled = false;
    button.textContent = isRead ? "Annuler le marquage" : "Marquer comme lu";
    status.textContent = `${book.title} : ${isRead
      ? "ce livre fait partie du vocabulaire initial."
      : "ce livre n’est pas encore inclus dans le vocabulaire initial."}`;
  }

  function makePathModel(path, targetId) {
    const target = booksById.get(targetId);
    return {
      target_title: target?.title ?? `book_${targetId}`,
      path_type: "shortest",
      steps: path.map((step, index) => {
        const book = booksById.get(String(step.id));
        return {
          title: book?.title ?? step.name,
          author: book?.author ?? "Project Gutenberg",
          cost: step.cost,
          status: index === path.length - 1
            ? "target"
            : index === 0
              ? "in_progress"
              : "upcoming",
        };
      }),
    };
  }

  function setPathStatus(message, isError = false) {
    const status = document.querySelector("#path-status");
    status.textContent = message;
    status.style.color = isError ? "var(--red)" : "var(--on-surface-variant)";
  }

  async function calculatePath() {
    const targetId = selectedTargetBookId;
    if (!targetId) {
      setPathStatus("Choisis d’abord un livre cible.", true);
      return;
    }

    const button = document.querySelector("#calculate-path");
    const threshold = Number(document.querySelector("#path-threshold").value) / 100;
    button.disabled = true;
    setPathStatus("Calcul du chemin en cours…");

    try {
      const response = await fetch(
        `${API.path}/${encodeURIComponent(targetId)}?comprehension_threshold=${threshold}`
      );
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `Erreur ${response.status}`);
      }
      if (!Array.isArray(result)) {
        throw new Error("Réponse inattendue de l’API de parcours.");
      }

      renderWorkflowSteps([]);
      if (result.length === 0) {
        renderPath(null);
        setPathStatus(readBookIds.has(targetId)
          ? "La cible est déjà marquée comme lue : aucun livre n’est à ajouter."
          : "Aucun chemin trouvé pour cette cible et ce seuil.");
        return;
      }

      const path = makePathModel(result, targetId);
      renderPath(path);
      renderWorkflowSteps(path.steps);
      setPathStatus(`${result.length} livre${result.length > 1 ? "s" : ""} dans le chemin calculé.`);
    } catch (error) {
      console.error("Unable to calculate the reading path:", error);
      setPathStatus(`Échec du calcul : ${error.message}`, true);
    } finally {
      button.disabled = false;
    }
  }

  async function toggleReadBook() {
    const bookId = selectedReadBookId;
    if (!bookId) {
      return;
    }

    const isRead = readBookIds.has(bookId);
    const button = document.querySelector("#toggle-read-book");
    button.disabled = true;
    try {
      const response = await fetch(`${API.readBooks}/${encodeURIComponent(bookId)}`, {
        method: isRead ? "DELETE" : "PUT",
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `Erreur ${response.status}`);
      }

      if (result.is_read) readBookIds.add(bookId);
      else readBookIds.delete(bookId);

      const [profile, readBooks] = await Promise.all([
        getJSON(API.profile),
        getJSON(API.readBooks),
      ]);
      readBookIds = new Set(readBooks.map(book => normalizeBookId(book.id)));
      const targetId = selectedTargetBookId;
      const target = booksById.get(targetId);
      renderProfile(profile, target?.title ?? "aucun");
      renderReadBooks(readBooks);
      renderReadHistory(readBooks);
      updateReadBookAction();
      document.querySelector("#read-state-status").textContent = result.is_read
        ? "Livre marqué comme lu ; son vocabulaire sera pris en compte."
        : "Marquage annulé ; le vocabulaire de ce livre ne sera plus initial.";

      if (targetId) {
        await calculatePath();
      }
    } catch (error) {
      console.error("Unable to update the reading state:", error);
      document.querySelector("#read-state-status").textContent =
        `Échec de la mise à jour : ${error.message}`;
      document.querySelector("#read-state-status").style.color = "var(--red)";
    } finally {
      updateReadBookAction();
    }
  }

  // ---------- Préférences ----------
  function renderPreferences(p) {
    const shown = p.genres.slice(0, 4);
    const rest = p.genres.length - shown.length;
    const genres = document.querySelector(".prefs .genres");
    genres.replaceChildren(...shown.map(g => el("span", "pill", GENRES[g] ?? g)));
    if (rest > 0) genres.append(el("span", "pill more", `+ ${rest}`));
    const n = p.favorite_books.length;
    renderMinis(n);
    document.querySelector("#liked-count").textContent = `${n} livre${n > 1 ? "s" : ""} aimé${n > 1 ? "s" : ""}`;
  }

  // ---------- Lancement ----------
  async function init() {
    try {
      const [profile, readBooks, catalogData, preferences] = await Promise.all([
        getJSON(API.profile),
        getJSON(API.readBooks),
        getJSON(API.books),
        getJSON(API.preferences),
      ]);
      populateBookControls(catalogData.books, readBooks);
      renderProfile(profile, "aucun");
      renderReadBooks(readBooks);
      renderReadHistory(readBooks);
      renderPath(null);
      renderPreferences(preferences);
    } catch (error) {
      console.error(error);
      showError("Impossible de charger les données : l'API est-elle lancée ?");
    }
  }

  document.querySelector("#target-book-search").addEventListener("input", event => {
    selectedTargetBookId = "";
    renderPath(null);
    renderWorkflowSteps([]);
    setPathStatus("Choisis un livre cible puis lance le calcul.");
    renderBookSearchResults(
      event.target.value,
      "target-book-results",
      "target-book-search-status",
      selectTargetBook
    );
  });
  document.querySelector("#read-book-search").addEventListener("input", event => {
    selectedReadBookId = "";
    updateReadBookAction();
    renderBookSearchResults(
      event.target.value,
      "read-book-results",
      "read-book-search-status",
      selectReadBook,
      true
    );
  });
  document.querySelector("#toggle-read-book").addEventListener("click", toggleReadBook);
  document.querySelector("#calculate-path").addEventListener("click", calculatePath);
  document.querySelector("#path-threshold").addEventListener("input", event => {
    document.querySelector("#threshold-value").textContent = event.target.value;
  });

  init();
})();