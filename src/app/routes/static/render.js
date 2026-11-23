const svg = d3.select("svg");
let width = svg.node().clientWidth;
let height = svg.node().clientHeight;

const linkLayer = svg.append("g").attr("stroke", "#999");
const nodeLayer = svg.append("g");

let books = [];
let allLinks = [];
let nodes = [];
let linkSel = null;
let nodeSel = null;
let selectedNodeId = null;
let readBookIds = new Set();
let directLinks = [];
let pathLinks = [];
let viewMode = "person";
let bookViewSourceId = null;

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink()
    .id(d => d.id)
    .distance(d => 220 - d.similarity * 180)
    .strength(d => 0.2 + d.similarity * 1.8))
  .force("charge", d3.forceManyBody().strength(-30))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .on("tick", ticked);

function getBookId(name) {
  const match = /^book_(\d+)$/.exec(name);
  return match ? Number(match[1]) : null;
}

async function apiFetch(path) {
  const localHost = ["127.0.0.1", "localhost"].includes(window.location.hostname);
  const bases = localHost ? [""] : ["http://127.0.0.1:8000"];

  for (const base of bases) {
    try {
      const response = await fetch(`${base}${path}`);
      return response;
    } catch (error) {
      continue;
    }
  }

  throw new Error(`Unable to reach the API at ${path}`);
}

async function loadGraph() {
  try {
    const booksResponse = await apiFetch("/api/books");
    const booksData = await booksResponse.json();
    books = booksData.books
      .map(book => {
        const id = getBookId(book.name);
        return id === null ? null : {
          id: String(id),
          title: book.name,
        };
      })
      .filter(book => book !== null);

    const similaritiesResponse = await apiFetch("/api/similarities");
    const similaritiesData = await similaritiesResponse.json();
    allLinks = similaritiesData.links.map(link => ({
      source: String(link.source),
      target: String(link.target),
      threshold: link.similar_percent * 100,
      similarity: link.similar_percent,
    }));

    const readBooksResponse = await apiFetch("/api/read-books");
    const readBooksData = await readBooksResponse.json();
    readBookIds = new Set(
      readBooksData.map(book => String(book.id))
    );

    nodes = [
      { id: "you", title: "you", kind: "user" },
      ...books.map(book => ({
        ...book,
        kind: readBookIds.has(book.id) ? "read" : "book",
      })),
    ];

    await loadDirectLinks();
    simulation.nodes(nodes);
    update(+d3.select("#seuil").property("value"));
  } catch (error) {
    console.error("Unable to load the graph:", error);
  }
}

async function loadDirectLinks() {
  directLinks = [];

  if (readBookIds.size === 0) {
    return;
  }

  for (const readBookId of readBookIds) {
    directLinks.push({
      source: "you",
      target: readBookId,
      threshold: 100,
      similarity: 1,
    });

    for (const book of books) {
      if (readBookId === book.id) {
        continue;
      }

      try {
        const response = await apiFetch(
          `/api/similarity/${readBookId}/${book.id}`
        );
        const data = await response.json();
        const similarity = data.similar_percent;
        const threshold = similarity * 100;
        directLinks.push({
          source: "you",
          target: book.id,
          threshold,
          similarity,
        });
      } catch (error) {
        console.error(
          `Unable to calculate direct similarity for ${readBookId} -> ${book.id}:`,
          error
        );
      }
    }
  }

  const strongestLinks = new Map();
  for (const link of directLinks) {
    const current = strongestLinks.get(link.target);
    if (!current || link.similarity > current.similarity) {
      strongestLinks.set(link.target, link);
    }
  }
  directLinks = [...strongestLinks.values()];
}

async function showShortestPath(bookId) {
  if (readBookIds.has(bookId)) {
    pathLinks = [{
      source: "you",
      target: bookId,
      threshold: 100,
      similarity: 1,
      path: true,
    }];
    update(+d3.select("#seuil").property("value"));
    return;
  }

  try {
    const threshold = +d3.select("#seuil").property("value");
    const comprehensionThreshold = Number(
      Math.min(1, Math.max(0, threshold / 100)).toFixed(4)
    );
    if (!Number.isFinite(comprehensionThreshold)) {
      throw new Error("Invalid comprehension threshold");
    }

    const params = new URLSearchParams({
      comprehension_threshold: String(comprehensionThreshold),
    });
    const response = await apiFetch(
      `/api/path/${encodeURIComponent(bookId)}?${params.toString()}`
    );
    const path = await response.json();
    if (!response.ok) {
      throw new Error(path.detail || "Unable to calculate the path");
    }
    if (!Array.isArray(path)) {
      throw new Error("The path API returned an invalid response");
    }

    pathLinks = [];
    let previousId = "you";
    for (const step of path) {
      const stepId = String(step.id);
      if (stepId === previousId) {
        continue;
      }
      pathLinks.push({
        source: previousId,
        target: stepId,
        threshold: 100,
        similarity: 1,
        path: true,
      });
      previousId = stepId;
    }
  } catch (error) {
    console.error(`Unable to calculate the path to ${bookId}:`, error);
    pathLinks = [];
  }

  update(+d3.select("#seuil").property("value"));
}

function update(threshold) {
  let links;

  if (viewMode === "book") {
    links = [
      ...allLinks,
      ...directLinks,
    ]
      .filter(link => link.threshold >= threshold)
      .filter(link =>
        bookViewSourceId === null ||
        link.source === bookViewSourceId ||
        link.target === bookViewSourceId
      )
      .map(link => ({ ...link }));
  } else if (selectedNodeId === null) {
    links = directLinks
      .filter(link => link.threshold >= threshold)
      .map(link => ({ ...link }));
  } else {
    links = pathLinks.map(link => ({ ...link }));
  }

  linkSel = linkLayer.selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", d => d.path ? 5 : 6 - d.threshold / 20)
    .attr("stroke", d => d.path ? "#d95f02" : d3.interpolateRdYlGn(d.threshold / 100))
    .attr("title", d =>
      `Similarity: ${(d.similarity * 100).toFixed(1)}%`
    );

  nodeSel = nodeLayer.selectAll("g")
    .data(nodes, d => d.id)
    .join(enter => {
      const g = enter.append("g").call(drag(simulation));
      g.append("circle").attr("r", d =>
        d.kind === "user" ? 18 : d.kind === "read" ? 16 : 14
      ).attr("fill", d =>
        d.kind === "user"
          ? "#6a3d9a"
          : d.kind === "read"
            ? "#2c7fb8"
            : "steelblue"
      );
      g.append("text").attr("dy", 28).attr("text-anchor", "middle").text(d => d.title);
      return g;
    });

  nodeSel
    .on("click", (event, d) => {
      event.stopPropagation();
      if (viewMode === "book") {
        if (d.kind === "user") {
          selectedNodeId = "you";
          bookViewSourceId = null;
          d3.select("#view-toggle").text("View: all books");
          update(threshold);
          return;
        }
        bookViewSourceId = d.id;
        selectedNodeId = d.id;
        update(threshold);
        d3.select("#view-toggle").text("View: all books");
        return;
      }

      if (d.kind === "user") {
        selectedNodeId = null;
        pathLinks = [];
        update(threshold);
        return;
      }

      if (selectedNodeId === d.id) {
        selectedNodeId = null;
        pathLinks = [];
        update(threshold);
        return;
      }

      selectedNodeId = d.id;
      showShortestPath(d.id);
    })
    .select("circle")
    .attr("fill", d => {
      if (d.id === selectedNodeId) return "#d95f02";
      if (d.kind === "user") return "#6a3d9a";
      if (d.kind === "read") return "#2c7fb8";
      return "steelblue";
    });

  simulation.force("link").links(links);
  simulation.alpha(1).restart();
}

function ticked() {
  if (linkSel) {
    linkSel
      .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  }
  if (nodeSel) {
    nodeSel.attr("transform", d => {
      const radius = d.kind === "user" ? 18 : d.kind === "read" ? 16 : 14;
      d.x = Math.max(radius, Math.min(width - radius, d.x));
      d.y = Math.max(radius, Math.min(height - radius, d.y));
      return `translate(${d.x},${d.y})`;
    });
  }
}

function drag(sim) {
  return d3.drag()
    .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (e, d) => {
      const radius = d.kind === "user" ? 18 : d.kind === "read" ? 16 : 14;
      d.fx = Math.max(radius, Math.min(width - radius, e.x));
      d.fy = Math.max(radius, Math.min(height - radius, e.y));
    })
    .on("end",   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; });
}

function setThreshold(value) {
  if (!Number.isFinite(value)) {
    return;
  }

  const threshold = Math.min(100, Math.max(0, value));
  d3.select("#seuil").property("value", threshold);
  d3.select("#seuil-number").property("value", threshold);
  d3.select("#val").text(String(threshold));
  update(threshold);
}

d3.select("#seuil").on("input", function () {
  setThreshold(+this.value);
});

d3.select("#seuil-number").on("input", function () {
  if (this.value !== "" && this.validity.valid) {
    setThreshold(+this.value);
  }
});

d3.select("#seuil-number").on("change", function () {
  if (this.value === "") {
    setThreshold(0);
  } else {
    setThreshold(+this.value);
  }
});

d3.select("#view-toggle").on("click", () => {
  const threshold = +d3.select("#seuil").property("value");

  if (viewMode === "person") {
    viewMode = "book";
    bookViewSourceId = null;
    selectedNodeId = null;
    pathLinks = [];
    d3.select("#view-toggle").text("View: all books");
  } else {
    viewMode = "person";
    bookViewSourceId = null;
    selectedNodeId = null;
    pathLinks = [];
    d3.select("#view-toggle").text("View: person");
  }

  update(threshold);
});

svg.on("click", event => {
  if (event.target !== svg.node() || selectedNodeId === null) {
    return;
  }
  selectedNodeId = null;
  update(+d3.select("#seuil").property("value"));
});

window.addEventListener("resize", () => {
  width = svg.node().clientWidth;
  height = svg.node().clientHeight;
  simulation
    .force("center", d3.forceCenter(width / 2, height / 2))
    .alpha(0.3)
    .restart();
});

loadGraph();