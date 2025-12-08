const API_BASE = "https://fa32941f-75f6-471c-a3a8-a5244783ebea-00-3sb8arows0wd3.sisko.replit.dev";
const STATUS_VARIANTS = ["info", "success", "error", "loading"];

document.addEventListener("DOMContentLoaded", () => {
  const dom = {
    substationsTableBody: document.querySelector("#substations-table tbody"),
    switchgearsTableBody: document.querySelector("#switchgears-table tbody"),
    substationsStatus: document.getElementById("substations-status"),
    switchgearsStatus: document.getElementById("switchgears-status"),
    substationForm: document.getElementById("create-substation-form"),
    substationFormStatus: document.getElementById("create-substation-status"),
    switchgearForm: document.getElementById("create-switchgear-form"),
    switchgearFormStatus: document.getElementById("create-switchgear-status"),
    switchgearSubstationSelect: document.querySelector(
      "#create-switchgear-form select[name='substation_id']"
    ),
  };

  setupAccordions();
  setupScrollShortcuts();
  attachEventHandlers(dom);

  loadSubstations(dom);
  loadSwitchgears(dom);
});

function attachEventHandlers(dom) {
  document.getElementById("refresh-substations")?.addEventListener("click", () =>
    loadSubstations(dom)
  );

  document.getElementById("refresh-switchgears")?.addEventListener("click", () =>
    loadSwitchgears(dom)
  );

  dom.substationForm?.addEventListener("submit", (event) =>
    handleSubstationSubmit(event, dom)
  );

  dom.switchgearForm?.addEventListener("submit", (event) =>
    handleSwitchgearSubmit(event, dom)
  );
}

async function loadSubstations(dom) {
  showTablePlaceholder(dom.substationsTableBody, "Загрузка подстанций...");
  setStatus(dom.substationsStatus, "Загрузка подстанций...", "loading");

  try {
    const payload = await fetchJSON("/api/objects/substations");
    const substations = normalizeList(payload);
    renderSubstations(substations, dom);
    setStatus(
      dom.substationsStatus,
      `Список обновлён · ${substations.length || 0} подстанц.`,
      "success"
    );
  } catch (error) {
    console.error("Substations load error", error);
    setStatus(dom.substationsStatus, extractErrorMessage(error), "error");
    showTablePlaceholder(dom.substationsTableBody, "Ошибка загрузки данных");
  }
}

async function loadSwitchgears(dom) {
  showTablePlaceholder(dom.switchgearsTableBody, "Загрузка КРУ...");
  setStatus(dom.switchgearsStatus, "Загрузка КРУ...", "loading");

  try {
    const payload = await fetchJSON("/api/objects/switchgears");
    const switchgears = normalizeList(payload);
    renderSwitchgears(switchgears, dom);
    setStatus(
      dom.switchgearsStatus,
      `Список обновлён · ${switchgears.length || 0} КРУ`,
      "success"
    );
  } catch (error) {
    console.error("Switchgears load error", error);
    setStatus(dom.switchgearsStatus, extractErrorMessage(error), "error");
    showTablePlaceholder(dom.switchgearsTableBody, "Ошибка загрузки данных");
  }
}

function renderSubstations(items, dom) {
  if (!dom.substationsTableBody) return;

  if (!items?.length) {
    showTablePlaceholder(dom.substationsTableBody, "Подстанции не найдены");
    updateSubstationOptions(items, dom);
    return;
  }

  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const row = document.createElement("tr");
    appendCell(row, item.id ?? "—");
    appendCell(row, item.name ?? "Без имени");
    appendCell(row, item.voltage_level ?? "—");
    appendCell(row, item.location ?? "—");
    appendCell(row, formatSwitchgearLabel(item.switchgears));
    fragment.appendChild(row);
  });

  dom.substationsTableBody.textContent = "";
  dom.substationsTableBody.appendChild(fragment);
  updateSubstationOptions(items, dom);
}

function renderSwitchgears(items, dom) {
  if (!dom.switchgearsTableBody) return;

  if (!items?.length) {
    showTablePlaceholder(dom.switchgearsTableBody, "КРУ не найдены");
    return;
  }

  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const row = document.createElement("tr");
    appendCell(row, item.id ?? "—");
    appendCell(row, item.name ?? "Без имени");
    appendCell(row, item.voltage ?? item.voltage_level ?? "—");
    appendCell(row, formatSubstationLabel(item));
    fragment.appendChild(row);
  });

  dom.switchgearsTableBody.textContent = "";
  dom.switchgearsTableBody.appendChild(fragment);
}

function updateSubstationOptions(items = [], dom) {
  const select = dom.switchgearSubstationSelect;
  if (!select) return;

  const currentValue = select.value;
  select.textContent = "";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Выберите подстанцию";
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);

  let isValuePreserved = false;

  items.forEach((item) => {
    if (item?.id == null) return;
    const option = document.createElement("option");
    option.value = String(item.id);
    const suffix = item.voltage_level ? ` · ${item.voltage_level}` : "";
    option.textContent = `${item.name ?? "Подстанция"}${suffix}`;
    if (String(item.id) === currentValue) {
      option.selected = true;
      placeholder.selected = false;
      isValuePreserved = true;
    }
    select.appendChild(option);
  });

  select.disabled = items.length === 0;

  if (!isValuePreserved && placeholder) {
    placeholder.selected = true;
  }
}

async function handleSubstationSubmit(event, dom) {
  event.preventDefault();
  const form = event.currentTarget;
  const submitButton = form.querySelector("button[type='submit']");
  const payload = serializeForm(form);

  toggleButtonLoading(submitButton, true, "Создаём...");
  setStatus(dom.substationFormStatus, "Отправляем данные...", "loading");

  try {
    await fetchJSON("/api/objects/substations", {
      method: "POST",
      body: payload,
    });

    form.reset();
    setStatus(dom.substationFormStatus, "Подстанция создана", "success");
    await loadSubstations(dom);
  } catch (error) {
    setStatus(dom.substationFormStatus, extractErrorMessage(error), "error");
  } finally {
    toggleButtonLoading(submitButton, false);
  }
}

async function handleSwitchgearSubmit(event, dom) {
  event.preventDefault();
  const form = event.currentTarget;
  const submitButton = form.querySelector("button[type='submit']");
  const payload = serializeForm(form);

  if (payload.substation_id) {
    payload.substation_id = Number(payload.substation_id);
  }

  toggleButtonLoading(submitButton, true, "Создаём...");
  setStatus(dom.switchgearFormStatus, "Отправляем данные...", "loading");

  try {
    await fetchJSON("/api/objects/switchgears", {
      method: "POST",
      body: payload,
    });

    form.reset();
    setStatus(dom.switchgearFormStatus, "КРУ создано", "success");
    await Promise.all([loadSwitchgears(dom), loadSubstations(dom)]);
  } catch (error) {
    setStatus(dom.switchgearFormStatus, extractErrorMessage(error), "error");
  } finally {
    toggleButtonLoading(submitButton, false);
  }
}

function setupAccordions() {
  document.querySelectorAll(".accordion-trigger").forEach((trigger) => {
    const targetId = trigger.getAttribute("data-target");
    if (!targetId) return;
    const panel = document.getElementById(targetId);
    if (!panel) return;

    if (!trigger.hasAttribute("aria-expanded")) {
      trigger.setAttribute("aria-expanded", "false");
    }

    const isExpanded = trigger.getAttribute("aria-expanded") === "true";
    panel.hidden = !isExpanded;

    trigger.addEventListener("click", () => {
      const expanded = trigger.getAttribute("aria-expanded") === "true";
      trigger.setAttribute("aria-expanded", String(!expanded));
      panel.hidden = expanded;
      const label = trigger.querySelector(".toggle-label");
      if (label) {
        label.textContent = expanded ? "Развернуть" : "Свернуть";
      }
    });
  });
}

function setupScrollShortcuts() {
  document.querySelectorAll("[data-scroll-target]").forEach((element) => {
    element.addEventListener("click", () => {
      const selector = element.getAttribute("data-scroll-target");
      if (!selector) return;
      const target = document.querySelector(selector);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function serializeForm(form) {
  const formData = new FormData(form);
  const payload = {};
  formData.forEach((value, key) => {
    if (typeof value === "string") {
      payload[key] = value.trim();
    } else {
      payload[key] = value;
    }
  });
  return payload;
}

function showTablePlaceholder(tbody, message) {
  if (!tbody) return;
  const table = tbody.closest("table");
  const columns = table?.querySelectorAll("th").length || 1;
  tbody.textContent = "";
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = columns;
  cell.className = "placeholder";
  cell.textContent = message;
  row.appendChild(cell);
  tbody.appendChild(row);
}

function appendCell(row, content) {
  const cell = document.createElement("td");
  cell.textContent = content ?? "—";
  row.appendChild(cell);
}

function formatSwitchgearLabel(value) {
  if (Array.isArray(value) && value.length) {
    return value
      .map((entry) => entry?.name ?? entry?.id ?? "—")
      .slice(0, 3)
      .join(", ") + (value.length > 3 ? ` +${value.length - 3}` : "");
  }
  if (typeof value === "number") {
    return `${value} ед.`;
  }
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  return "—";
}

function formatSubstationLabel(switchgear) {
  if (!switchgear) return "—";
  if (typeof switchgear.substation_name === "string") {
    return switchgear.substation_name;
  }
  if (switchgear.substation) {
    const reference = switchgear.substation;
    if (typeof reference === "string") {
      return reference;
    }
    if (typeof reference === "object") {
      return reference.name ?? reference.title ?? (reference.id != null ? `ID ${reference.id}` : "—");
    }
  }
  if (typeof switchgear.substation === "string") {
    return switchgear.substation;
  }
  if (switchgear.substation_id != null) {
    return `ID ${switchgear.substation_id}`;
  }
  return "—";
}

function toggleButtonLoading(button, isLoading, loadingText) {
  if (!button) return;
  if (isLoading) {
    button.dataset.defaultLabel = button.textContent;
    button.disabled = true;
    if (loadingText) {
      button.textContent = loadingText;
    }
  } else {
    button.disabled = false;
    if (button.dataset.defaultLabel) {
      button.textContent = button.dataset.defaultLabel;
      delete button.dataset.defaultLabel;
    }
  }
}

async function fetchJSON(path, options = {}) {
  const config = { ...options };
  config.headers = {
    Accept: "application/json",
    ...(options.headers || {}),
  };

  if (config.body && !(config.body instanceof FormData) && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }

  if (config.body && !(config.body instanceof FormData)) {
    config.headers["Content-Type"] ??= "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, config);
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  let data;

  try {
    data = isJson ? await response.json() : await response.text();
  } catch (parseError) {
    data = null;
  }

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : data?.detail || data?.message || `Ошибка API (${response.status})`;
    const error = new Error(message);
    error.payload = data;
    error.status = response.status;
    throw error;
  }

  return data;
}

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload?.items && Array.isArray(payload.items)) return payload.items;
  if (payload?.data && Array.isArray(payload.data)) return payload.data;
  if (payload?.results && Array.isArray(payload.results)) return payload.results;
  return [];
}

function setStatus(target, message, type = "info") {
  if (!target) return;
  if (!message) {
    target.textContent = "";
    target.hidden = true;
    return;
  }

  target.hidden = false;
  target.textContent = message;
  STATUS_VARIANTS.forEach((variant) =>
    target.classList.remove(`is-${variant}`)
  );
  target.classList.add(`is-${type}`);
}

function extractErrorMessage(error) {
  if (!error) return "Неизвестная ошибка";
  if (typeof error === "string") return error;
  if (error.detail) return error.detail;
  if (error.message) return error.message;
  return "Произошла ошибка";
}
