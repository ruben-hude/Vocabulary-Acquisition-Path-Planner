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

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink().id(d => d.id).distance(d => 40 + d.threshold * 1.5))
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
      if (response.ok) {
        return response;
      }
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

    nodes = books.map(book => ({ ...book }));

    const similaritiesResponse = await apiFetch("/api/similarities");
    const similaritiesData = await similaritiesResponse.json();
    const links = similaritiesData.links.map(link => ({
      source: String(link.source),
      target: String(link.target),
      threshold: link.similar_percent * 100,
      similarity: link.similar_percent,
    }));

    allLinks = links;
    simulation.nodes(nodes);
    update(+d3.select("#seuil").property("value"));
  } catch (error) {
    console.error("Unable to load the graph:", error);
  }
}

function update(threshold) {
  const links = allLinks
    .filter(l => l.threshold >= threshold)
    .filter(l =>
      selectedNodeId === null ||
      l.source === selectedNodeId ||
      l.target === selectedNodeId
    )
    .map(l => ({ ...l }));

  linkSel = linkLayer.selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", d => 6 - d.threshold / 20)
    .attr("stroke", d => d3.interpolateRdYlGn(d.threshold / 100))
    .attr("title", d =>
      `Similarity: ${(d.similarity * 100).toFixed(1)}%`
    );

  nodeSel = nodeLayer.selectAll("g")
    .data(nodes, d => d.id)
    .join(enter => {
      const g = enter.append("g").call(drag(simulation));
      g.append("circle").attr("r", 14).attr("fill", "steelblue");
      g.append("text").attr("dy", 28).attr("text-anchor", "middle").text(d => d.title);
      return g;
    });

  nodeSel
    .on("click", (event, d) => {
      event.stopPropagation();
      selectedNodeId = selectedNodeId === d.id ? null : d.id;
      update(threshold);
    })
    .select("circle")
    .attr("fill", d => d.id === selectedNodeId ? "#d95f02" : "steelblue");

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
    nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
  }
}

function drag(sim) {
  return d3.drag()
    .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
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