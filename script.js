const modalTriggers = document.querySelectorAll('[data-modal-target]');
const modals = document.querySelectorAll('.modal');
const body = document.body;

const openModal = (selector) => {
  const modal = document.querySelector(selector);
  if (!modal) return;

  modal.classList.add('modal--visible');
  modal.setAttribute('aria-hidden', 'false');
  modal.setAttribute('aria-modal', 'true');
  body.style.overflow = 'hidden';
};

const closeModal = (modal) => {
  modal.classList.remove('modal--visible');
  modal.setAttribute('aria-hidden', 'true');
  modal.setAttribute('aria-modal', 'false');
  if (![...modals].some((m) => m.classList.contains('modal--visible'))) {
    body.style.overflow = '';
  }
};

const openTechWriterModal = () => openModal('#writerModal');
const closeTechWriterModal = () => {
  const modal = document.querySelector('#writerModal');
  if (modal) closeModal(modal);
};

const openPueSnipModal = () => openModal('#referenceModal');
const closePueSnipModal = () => {
  const modal = document.querySelector('#referenceModal');
  if (modal) closeModal(modal);
};

const openScannerModal = () => openModal('#scannerModal');
const closeScannerModal = () => {
  const modal = document.querySelector('#scannerModal');
  if (modal) closeModal(modal);
};

const openRelayProtectionModal = () => openModal('#assistantModal');
const closeRelayProtectionModal = () => {
  const modal = document.querySelector('#assistantModal');
  if (modal) closeModal(modal);
};

if (typeof window !== 'undefined') {
  window.openTechWriterModal = openTechWriterModal;
  window.closeTechWriterModal = closeTechWriterModal;
  window.openPueSnipModal = openPueSnipModal;
  window.closePueSnipModal = closePueSnipModal;
  window.openScannerModal = openScannerModal;
  window.closeScannerModal = closeScannerModal;
  window.openRelayProtectionModal = openRelayProtectionModal;
  window.closeRelayProtectionModal = closeRelayProtectionModal;
}

modalTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => {
    const target = trigger.getAttribute('data-modal-target');
    openModal(target);
  });
});

modals.forEach((modal) => {
  modal.addEventListener('click', (event) => {
    if (event.target.hasAttribute('data-modal-close')) {
      closeModal(modal);
    }
  });
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    modals.forEach((modal) => {
      if (modal.classList.contains('modal--visible')) {
        closeModal(modal);
      }
    });
  }
});

const setChipFeedback = (button, message) => {
  if (!button) return;
  const label = button.querySelector('.chip__label');
  const original = button.dataset.label;
  if (!label || !original) return;
  label.textContent = message;
  button.classList.add('is-busy');
  setTimeout(() => {
    label.textContent = original;
    button.classList.remove('is-busy');
  }, 1500);
};

// --- Tech Writer modal ---
const writerStageOrder = ['input', 'analysis', 'generation', 'done'];
const writerStages = document.querySelectorAll('[data-writer-stage]');
const techWriterForm = document.getElementById('techWriterForm');
const writerLogList = document.getElementById('techWriterLog');
const writerTimerEl = document.getElementById('writerTimer');
const writerDropzone = document.getElementById('techWriterDropzone');
const writerFileInput = document.getElementById('techWriterFiles');
const writerFileList = document.getElementById('techWriterFileList');
let writerTimer = null;
let writerElapsed = 0;
let writerIsBusy = false;
let writerFiles = [];

const formatSize = (bytes) => {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const updateWriterFiles = (files) => {
  writerFiles = files;
  if (!writerFileList) return;
  writerFileList.innerHTML = '';
  writerFiles.forEach((file) => {
    const li = document.createElement('li');
    li.textContent = `${file.name} · ${formatSize(file.size)}`;
    writerFileList.appendChild(li);
  });
};

const handleWriterFiles = (fileList) => {
  const files = Array.from(fileList).slice(0, 8);
  updateWriterFiles(files);
};

const startWriterTimer = () => {
  if (!writerTimerEl) return;
  const start = Date.now();
  writerTimerEl.textContent = '00:00';
  writerElapsed = 0;
  writerTimer = setInterval(() => {
    writerElapsed = Date.now() - start;
    const seconds = Math.floor(writerElapsed / 1000);
    const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
    const secs = String(seconds % 60).padStart(2, '0');
    writerTimerEl.textContent = `${mins}:${secs}`;
  }, 1000);
};

const stopWriterTimer = () => {
  if (writerTimer) {
    clearInterval(writerTimer);
    writerTimer = null;
  }
};

const setWriterStage = (stageKey) => {
  const stageIndex = writerStageOrder.indexOf(stageKey);
  writerStages.forEach((stageEl) => {
    const currentKey = stageEl.dataset.writerStage;
    stageEl.classList.remove('is-active', 'is-complete');
    const currentIndex = writerStageOrder.indexOf(currentKey);
    if (currentIndex < stageIndex) {
      stageEl.classList.add('is-complete');
    }
    if (currentIndex === stageIndex) {
      stageEl.classList.add('is-active');
    }
  });
};

const pushWriterLog = (message) => {
  if (!writerLogList) return;
  const item = document.createElement('li');
  const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  item.textContent = `[${time}] ${message}`;
  writerLogList.prepend(item);
  const maxItems = 10;
  while (writerLogList.children.length > maxItems) {
    writerLogList.removeChild(writerLogList.lastElementChild);
  }
};

const writerPipeline = (
  docType,
  productName,
) => [
  { stage: 'input', delay: 300, message: `Паспорт изделия ${productName} принят` },
  { stage: 'analysis', delay: 900, message: 'Сверка ERP, проверка ГОСТ и комплектности' },
  { stage: 'analysis', delay: 1600, message: 'AI-анализ проводит текстовую нормализацию' },
  { stage: 'generation', delay: 2300, message: `Формирование шаблона: ${docType}` },
  { stage: 'generation', delay: 3200, message: 'Сборка таблиц, графиков и ссылок на нормативы' },
  { stage: 'done', delay: 4200, message: 'Документы подписаны ЭП и сохранены в архиве AIтехник' },
];

if (writerStages.length) {
  setWriterStage('input');
}

if (writerDropzone && writerFileInput) {
  ['click'].forEach((evt) => {
    writerDropzone.addEventListener(evt, () => writerFileInput.click());
  });

  ['dragenter', 'dragover'].forEach((evt) => {
    writerDropzone.addEventListener(evt, (event) => {
      event.preventDefault();
      writerDropzone.classList.add('is-dragover');
    });
  });

  ['dragleave', 'drop'].forEach((evt) => {
    writerDropzone.addEventListener(evt, (event) => {
      event.preventDefault();
      writerDropzone.classList.remove('is-dragover');
      if (evt === 'drop' && event.dataTransfer) {
        handleWriterFiles(event.dataTransfer.files);
      }
    });
  });

  writerFileInput.addEventListener('change', (event) => {
    if (!event.target.files) return;
    handleWriterFiles(event.target.files);
  });
}

if (techWriterForm) {
  techWriterForm.addEventListener('submit', (event) => {
    event.preventDefault();
    if (writerIsBusy) return;
    const submitButton = techWriterForm.querySelector('button[type="submit"]');
    const formData = new FormData(techWriterForm);
    const docType = formData.get('docType');
    const productName = formData.get('productName');
    writerIsBusy = true;
    startWriterTimer();
    setWriterStage('input');
    pushWriterLog(`Старт генерации комплекта «${docType}» для ${productName}`);
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Генерация…';
    }

    const steps = writerPipeline(docType, productName);
    let accumulatedDelay = 0;
    steps.forEach((step, index) => {
      accumulatedDelay += step.delay;
      setTimeout(() => {
        setWriterStage(step.stage);
        pushWriterLog(step.message);
        if (index === steps.length - 1) {
          writerIsBusy = false;
          stopWriterTimer();
          if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Запустить генерацию';
          }
          pushWriterLog('Готово. Архив доступен в AL Drive.');
        }
      }, accumulatedDelay);
    });
  });
}

// --- Reference modal ---
const referenceData = {
  pue: [
    {
      id: 'pue-1',
      section: 'Раздел 1',
      title: 'Общие положения',
      chapter: 'Глава 1.2 «Электроснабжение и электрические сети»',
      summary:
        'Глава определяет требования к надежности электроснабжения, допустимым отклонениям напряжения и классификации потребителей по категориям',
      highlights: [
        'Категории надежности I-III для потребителей',
        'Пределы отклонений напряжения ±5% в нормальном режиме',
        'Обязательная двухцепная схема питания для I категории',
      ],
      table: {
        head: ['Категория', 'Требование', 'Применение AIтехник'],
        rows: [
          ['I', 'Две независимые источника питания', 'Щиты собственных нужд и ИБП AIтехник'],
          ['II', 'Возможен перерыв до 24 ч', 'Цеховые линии и резервные вводы'],
          ['III', 'Допустим останов на время ремонта', 'Временные строительные сети'],
        ],
      },
    },
    {
      id: 'pue-2',
      section: 'Раздел 2',
      title: 'Устройства и сетевые решения',
      chapter: 'Глава 2.3 «Коммутационные аппараты»',
      summary: 'Определяет минимальные расстояния, требования к масломасляным и вакуумным аппаратам, ресурсы по операциям',
      highlights: [
        'Минимальные расстояния для шин 6-10 кВ — 90 мм',
        'Рекомендована вакуумная коммутация для частых операций',
      ],
      table: {
        head: ['Аппарат', 'Класс напряжения', 'Ресурс, циклов'],
        rows: [
          ['Выключатель ВВ/TEL-10', '10 кВ', '30 000'],
          ['Разъединитель РВЗ', '6 кВ', '10 000'],
          ['Контактор КВ-1М', '0,4 кВ', '100 000'],
        ],
      },
    },
    {
      id: 'pue-3',
      section: 'Раздел 3',
      title: 'Защитные меры безопасности',
      chapter: 'Глава 3.4 «Заземление и защитные проводники»',
      summary: 'Расписывает сопротивление заземляющих устройств, сечения защитных проводников и условия уравнивания потенциалов',
      highlights: [
        'Сопротивление заземления до 4 Ом для сетей 0,4 кВ',
        'Сечение РЕ не менее 16 мм² для меди',
      ],
      table: {
        head: ['Материал', 'Минимальное сечение, мм²', 'Примечание'],
        rows: [
          ['Медь', '16', 'Для кабельных линий AIтехник'],
          ['Алюминий', '25', 'Для сборных шин'],
          ['Сталь', '50', 'Ленточные заземлители'],
        ],
      },
    },
    {
      id: 'pue-4',
      section: 'Раздел 4',
      title: 'Релейная защита и автоматика',
      chapter: 'Глава 4.2 «Принципы уставок»',
      summary: 'Описывает расчет уставок МТЗ, ДЗ, требуемые коэффициенты чувствительности и резервирование от отказа',
      highlights: [
        'Коэффициент чувствительности по МТЗ ≥ 1,3',
        'Селективность обеспечивается запасом времени ≥ 0,2 с',
      ],
      table: {
        head: ['Тип защиты', 'Критерий', 'Рекомендация'],
        rows: [
          ['МТЗ', 'Iустав > 1,3·Iкзмин', 'Использовать отсечку'],
          ['ДЗ', 'Idiff/Itorm ≥ 1,2', 'Настроить торможение'],
          ['ТЗНП', 'Iустав = 0,6·I0', 'Контроль нулевой последовательности'],
        ],
      },
    },
    {
      id: 'pue-5',
      section: 'Раздел 5',
      title: 'Кабельные сети',
      chapter: 'Глава 5.5 «Прокладка в сооружениях»',
      summary: 'Условия выбора кабелей, допустимые температуры, требования к огнестойкости и маркировке',
      highlights: [
        'Использовать кабели НГ(А)-FRLS на объектах с категорией А/Б',
        'Температура жил не более 70 °C для ПВХ изоляции',
      ],
      table: {
        head: ['Марка', 'Способ прокладки', 'Доп. ток, А'],
        rows: [
          ['ВВГнг(А)-LS 3×95', 'Лоток', '270'],
          ['ПвВГнг(А)-FRLS 3×70', 'Канал', '230'],
        ],
      },
    },
    {
      id: 'pue-6',
      section: 'Раздел 6',
      title: 'Электроустановки особых помещений',
      chapter: 'Глава 6.1 «Взрывоопасные зоны»',
      summary: 'Классификация зон, требования к оболочкам, степень защиты и отключению питания',
      highlights: [
        'Зона В-1г требует Exd оборудования',
        'Автоматическое отключение питания ≤ 0,2 с',
      ],
      table: {
        head: ['Зона', 'Исполнение', 'Температурный класс'],
        rows: [
          ['0', 'Exia', 'T4'],
          ['1', 'Exd/Exe', 'T3'],
          ['2', 'Exn', 'T2'],
        ],
      },
    },
    {
      id: 'pue-7',
      section: 'Раздел 7',
      title: 'Специальные установки',
      chapter: 'Глава 7.1 «Трансформаторные подстанции»',
      summary: 'Регламентирует размещение КРУ/КСО, расстояния обслуживания, схемы собственных нужд',
      highlights: [
        'Минимальный коридор обслуживания 1,5 м',
        'Системы блокировок между ВВ и заземлителями обязательны',
      ],
      table: {
        head: ['Оборудование', 'Расстояние, м', 'Комментарии'],
        rows: [
          ['Камеры КСО', '1,5', 'Со стороны привода'],
          ['Шкафы РЗА', '0,8', 'Перекидной стол'],
        ],
      },
    },
  ],
  snip: [
    {
      id: 'snip-1',
      section: 'СП 31-110-2003',
      title: 'Проектирование и монтаж электроустановок жилых и общественных зданий',
      chapter: 'Глава 5 «Питающие сети»',
      summary: 'Требования по расчету нагрузок, равномерности фаз и резервированию бытовых вводов',
      highlights: [
        'Коэффициент спроса для жильцов 0,2-0,3',
        'Обязательный учет суммарной нагрузки лифтов и насосов',
      ],
      table: {
        head: ['Элемент', 'Расчётная мощность', 'Примечание'],
        rows: [
          ['Секция жилого дома', '6,5 кВт на квартиру', 'AL Smart Meter'],
          ['Пожарные насосы', 'По фактической', 'Коэффициент 1,0'],
        ],
      },
    },
    {
      id: 'snip-2',
      section: 'СП 6.13130.2013',
      title: 'Электрооборудование специальных установок пожарной автоматики',
      chapter: 'Раздел 8 «Дымоудаление и подпор воздуха»',
      summary: 'Регламентирует схемы питания, селективность групп и требования к кабельным линиям пожарных систем',
      highlights: [
        'Отдельные вводы для систем пожаротушения',
        'Кабели огнестойкие не менее 180 мин (FRLS 1,8)',
      ],
      table: {
        head: ['Система', 'Класс линии', 'Время работы'],
        rows: [
          ['ДУ', 'FE180', '≥ 60 мин'],
          ['Пожарная сигнализация', 'E30', '≥ 30 мин'],
        ],
      },
    },
    {
      id: 'snip-3',
      section: 'СП 89.13330.2016',
      title: 'Электроустановки промышленных предприятий',
      chapter: 'Раздел 7 «Освещение»',
      summary: 'Нормы освещенности, схемы аварийного освещения и требования к автоматическому включению',
      highlights: [
        'Аварийное освещение ≥ 5% от рабочего',
        'Дублирование питания через АВР',
      ],
      table: {
        head: ['Помещение', 'Lux', 'Комментарий'],
        rows: [
          ['Щиты РЗА', '300', 'Равномерность 0,7'],
          ['Производственные цехи', '200', 'Светодиодные панели'],
        ],
      },
    },
  ],
};

const referenceNav = document.getElementById('referenceNav');
const referenceBody = document.getElementById('referenceBody');
const referenceSearchInput = document.getElementById('referenceSearch');
const referenceBookmarkBtn = document.getElementById('referenceBookmarkBtn');
const referenceCopyLinkBtn = document.getElementById('referenceCopyLinkBtn');
const bookmarkList = document.getElementById('bookmarkList');
const historyList = document.getElementById('historyList');
const referenceTabButtons = document.querySelectorAll('[data-reference-tab]');
const referencePanelButtons = document.querySelectorAll('[data-reference-panel]');
const referencePanelSections = document.querySelectorAll('[data-reference-section]');
let referenceCurrentTab = 'pue';
let referenceCurrentId = null;
const referenceBookmarks = [];
const referenceHistory = [];

const renderBookmarkList = () => {
  if (!bookmarkList) return;
  bookmarkList.innerHTML = '';
  if (!referenceBookmarks.length) {
    const empty = document.createElement('li');
    empty.textContent = 'Нет закладок';
    bookmarkList.appendChild(empty);
    return;
  }
  referenceBookmarks.forEach((entry) => {
    const li = document.createElement('li');
    li.textContent = `${entry.title} (${entry.section})`;
    li.addEventListener('click', () => setReferenceActive(entry.id));
    bookmarkList.appendChild(li);
  });
};

const renderHistoryList = () => {
  if (!historyList) return;
  historyList.innerHTML = '';
  if (!referenceHistory.length) {
    const empty = document.createElement('li');
    empty.textContent = 'История пуста';
    historyList.appendChild(empty);
    return;
  }
  referenceHistory.forEach((entry) => {
    const li = document.createElement('li');
    li.textContent = `${entry.time} · ${entry.title}`;
    li.addEventListener('click', () => setReferenceActive(entry.id));
    historyList.appendChild(li);
  });
};

const referenceMarkup = (entry) => {
  const highlightsList = entry.highlights
    .map((point) => `<li>${point}</li>`)
    .join('');
  const tableRows = entry.table.rows
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`)
    .join('');
  return `
    <header>
      <p class="modal-label">${entry.section}</p>
      <h2>${entry.title}</h2>
      <p>${entry.chapter}</p>
    </header>
    <p>${entry.summary}</p>
    <h4>Ключевые требования</h4>
    <ul>${highlightsList}</ul>
    <table class="reference-table">
      <thead>
        <tr>${entry.table.head.map((cell) => `<th>${cell}</th>`).join('')}</tr>
      </thead>
      <tbody>${tableRows}</tbody>
    </table>
  `;
};

const renderReferenceNav = () => {
  if (!referenceNav) return;
  const dataset = referenceData[referenceCurrentTab] || [];
  const search = referenceSearchInput ? referenceSearchInput.value.toLowerCase().trim() : '';
  referenceNav.innerHTML = '';
  const filtered = dataset.filter((entry) => {
    if (!search) return true;
    return (
      entry.section.toLowerCase().includes(search) ||
      entry.title.toLowerCase().includes(search) ||
      entry.chapter.toLowerCase().includes(search)
    );
  });

  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.className = 'reference-nav-empty';
    empty.textContent = 'Разделы не найдены';
    referenceNav.appendChild(empty);
    return;
  }

  filtered.forEach((entry) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'reference-nav-item';
    if (entry.id === referenceCurrentId) button.classList.add('is-active');
    button.innerHTML = `<strong>${entry.section}</strong><span>${entry.title}</span>`;
    button.addEventListener('click', () => setReferenceActive(entry.id));
    referenceNav.appendChild(button);
  });
};

const setReferenceActive = (id) => {
  const dataset = referenceData[referenceCurrentTab];
  const entry = dataset.find((item) => item.id === id) || dataset[0];
  if (!entry || !referenceBody) return;
  referenceCurrentId = entry.id;
  referenceBody.innerHTML = referenceMarkup(entry);
  renderReferenceNav();
  const timestamp = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  if (!referenceHistory.length || referenceHistory[0].id !== entry.id) {
    referenceHistory.unshift({ id: entry.id, title: entry.title, time: timestamp, section: entry.section });
    if (referenceHistory.length > 6) referenceHistory.pop();
    renderHistoryList();
  }
};

if (referenceSearchInput) {
  referenceSearchInput.addEventListener('input', () => renderReferenceNav());
}

referenceTabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    referenceTabButtons.forEach((btn) => btn.classList.remove('is-active'));
    button.classList.add('is-active');
    referenceCurrentTab = button.dataset.referenceTab;
    referenceCurrentId = null;
    renderReferenceNav();
    setReferenceActive(referenceData[referenceCurrentTab][0]?.id);
  });
});

if (referenceBookmarkBtn) {
  referenceBookmarkBtn.addEventListener('click', () => {
    const dataset = referenceData[referenceCurrentTab];
    const entry = dataset.find((item) => item.id === referenceCurrentId);
    if (!entry) return;
    const exists = referenceBookmarks.some((item) => item.id === entry.id);
    if (!exists) {
      referenceBookmarks.unshift({ id: entry.id, title: entry.title, section: entry.section });
      if (referenceBookmarks.length > 8) referenceBookmarks.pop();
      renderBookmarkList();
      setChipFeedback(referenceBookmarkBtn, 'Добавлено');
    }
  });
}

if (referenceCopyLinkBtn) {
  referenceCopyLinkBtn.addEventListener('click', async () => {
    const url = new URL(window.location.href);
    url.hash = referenceCurrentId || '';
    try {
      await navigator.clipboard.writeText(url.toString());
      setChipFeedback(referenceCopyLinkBtn, 'Скопировано');
    } catch (err) {
      console.error('Clipboard error', err);
    }
  });
}

const activateReferencePanel = (panelName) => {
  referencePanelSections.forEach((section) => {
    const isMatch = section.dataset.referenceSection === panelName;
    section.classList.toggle('is-active', isMatch);
  });
};

referencePanelButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const target = button.dataset.referencePanel;
    referencePanelButtons.forEach((btn) => btn.setAttribute('aria-pressed', btn === button ? 'true' : 'false'));
    activateReferencePanel(target);
    const panelSection = Array.from(referencePanelSections).find(
      (section) => section.dataset.referenceSection === target,
    );
    panelSection?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
});

if (referenceNav) {
  renderReferenceNav();
  setReferenceActive(referenceData[referenceCurrentTab][0]?.id);
  renderBookmarkList();
  renderHistoryList();
  activateReferencePanel('bookmarks');
}

// --- Scanner modal ---
const scannerDropzone = document.getElementById('scannerDropzone');
const scannerFileInput = document.getElementById('scannerFiles');
const scannerFileList = document.getElementById('scannerFileList');
const scannerStatus = document.getElementById('scannerStatus');
const scannerLog = document.getElementById('scannerLog');
const scannerActionButtons = document.querySelectorAll('[data-scanner-action]');
let scannerFiles = [];

const renderScannerFiles = () => {
  if (!scannerFileList) return;
  scannerFileList.innerHTML = '';
  if (!scannerFiles.length) {
    const empty = document.createElement('li');
    empty.textContent = 'Файлы не выбраны';
    scannerFileList.appendChild(empty);
    return;
  }
  scannerFiles.forEach((file) => {
    const li = document.createElement('li');
    li.textContent = `${file.name} · ${formatSize(file.size)}`;
    scannerFileList.appendChild(li);
  });
};

const pushScannerLog = (message) => {
  if (!scannerLog) return;
  const li = document.createElement('li');
  li.textContent = message;
  scannerLog.prepend(li);
  if (scannerLog.children.length > 8) {
    scannerLog.removeChild(scannerLog.lastElementChild);
  }
};

const handleScannerFiles = (fileList) => {
  const allowed = ['pdf', 'dwg', 'png', 'jpg', 'jpeg'];
  const maxSize = 50 * 1024 * 1024;
  const files = Array.from(fileList).filter((file) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    const validType = ext ? allowed.includes(ext) : false;
    const validSize = file.size <= maxSize;
    return validType && validSize;
  });
  scannerFiles = files;
  renderScannerFiles();
  if (files.length) {
    pushScannerLog(`Загружено файлов: ${files.length}`);
    if (scannerStatus) scannerStatus.textContent = 'Файлы готовы к анализу';
  }
};

if (scannerDropzone && scannerFileInput) {
  scannerDropzone.addEventListener('click', () => scannerFileInput.click());
  ['dragenter', 'dragover'].forEach((evt) => {
    scannerDropzone.addEventListener(evt, (event) => {
      event.preventDefault();
      scannerDropzone.classList.add('is-dragover');
    });
  });
  ['dragleave', 'drop'].forEach((evt) => {
    scannerDropzone.addEventListener(evt, (event) => {
      event.preventDefault();
      scannerDropzone.classList.remove('is-dragover');
      if (evt === 'drop' && event.dataTransfer) {
        handleScannerFiles(event.dataTransfer.files);
      }
    });
  });
  scannerFileInput.addEventListener('change', (event) => {
    if (event.target.files) handleScannerFiles(event.target.files);
  });
}

const scannerActionsMap = {
  spec: 'Сформирована спецификация оборудования',
  client: 'Подготовлены пояснения для клиента',
  'export-xl': 'Экспорт в Excel завершён',
  'export-pdf': 'PDF отчёт сформирован',
};

scannerActionButtons.forEach((button) => {
  button.addEventListener('click', () => {
    if (!scannerFiles.length) {
      pushScannerLog('Добавьте схемы перед запуском анализа');
      if (scannerStatus) scannerStatus.textContent = 'Нет файлов';
      return;
    }
    const action = button.dataset.scannerAction;
    if (scannerStatus) scannerStatus.textContent = 'Анализ...';
    button.disabled = true;
    setTimeout(() => {
      button.disabled = false;
      pushScannerLog(scannerActionsMap[action]);
      if (scannerStatus) scannerStatus.textContent = 'Анализ завершён';
    }, 1200);
  });
});

// --- RZA calculator ---
const rzaTabButtons = document.querySelectorAll('[data-rza-tab]');
const rzaPanels = document.querySelectorAll('[data-rza-panel]');
const rzaResultsContainer = document.getElementById('rzaResults');
const rzaExportButtons = document.querySelectorAll('[data-rza-export]');
const rzaSubstationSelect = document.getElementById('rzaSubstation');
const rzaSubstationInfo = document.getElementById('rzaSubstationInfo');

const substationInfo = {
  kru6: {
    title: 'КРУ-6 кВ',
    description: 'Компоновка с вакуумными выключателями, токи до 1250 А, применяются схемы двойной секции',
    scheme: 'Схема: Ввод AВР — Секционный выключатель — Фидеры',
  },
  kru10: {
    title: 'КРУ-10 кВ',
    description: 'Шкафы AIтехник серии AL-K, трансформаторы 2,5-6,3 МВА',
    scheme: 'Схема: Два ввода 110/10 кВ, дифференциальная защита секций',
  },
  kso10: {
    title: 'КСО-10 кВ',
    description: 'Камеры с выкатными элементами, токи до 630 А, повышенные требования к блокировкам',
    scheme: 'Схема: КСО-298 с ТТ класса 10Р',
  },
};

const renderSubstationInfo = (key) => {
  if (!rzaSubstationInfo) return;
  const info = substationInfo[key];
  if (!info) return;
  rzaSubstationInfo.innerHTML = `<strong>${info.title}</strong> · ${info.description}<br /><small>${info.scheme}</small>`;
};

const setActiveRzaTab = (tab) => {
  rzaTabButtons.forEach((btn) => btn.classList.remove('is-active'));
  rzaPanels.forEach((panel) => panel.classList.remove('is-active'));
  const targetPanel = document.querySelector(`[data-rza-panel="${tab}"]`);
  const targetButton = document.querySelector(`[data-rza-tab="${tab}"]`);
  if (targetPanel) targetPanel.classList.add('is-active');
  if (targetButton) targetButton.classList.add('is-active');
};

const renderRzaResult = (result) => {
  if (!rzaResultsContainer) return;
  if (rzaResultsContainer.firstElementChild?.tagName === 'P') {
    rzaResultsContainer.innerHTML = '';
  }
  const card = document.createElement('div');
  card.className = 'rza-result-card';
  const metrics = result.metrics
    .map((metric) => `<li><strong>${metric.label}:</strong> ${metric.value}</li>`)
    .join('');
  card.innerHTML = `
    <h5>${result.title}</h5>
    <ul>${metrics}</ul>
    <p>${result.note}</p>
  `;
  rzaResultsContainer.prepend(card);
  if (rzaResultsContainer.children.length > 4) {
    rzaResultsContainer.removeChild(rzaResultsContainer.lastElementChild);
  }
};

const calculateRza = (type, data) => {
  switch (type) {
    case 'mtz': {
      const inNom = Number(data.in);
      const ks = Number(data.ks);
      const t = Number(data.t);
      const iset = inNom * ks;
      return {
        title: 'МТЗ',
        metrics: [
          { label: 'Ток срабатывания', value: `${iset.toFixed(1)} A` },
          { label: 'Время задержки', value: `${t.toFixed(2)} c` },
        ],
        note: 'Проверить соответствие коэффициента чувствительности требованиям ПУЭ ≥ 1,3.',
      };
    }
    case 'dif': {
      const idiff = Number(data.idiff);
      const irestr = Number(data.irestr);
      const kh = Number(data.kh);
      const sensitivity = idiff / (irestr * (1 + kh));
      return {
        title: 'Дифзащита',
        metrics: [
          { label: 'Чувствительность', value: sensitivity.toFixed(2) },
          { label: 'Ток срабатывания', value: `${idiff.toFixed(1)} A` },
        ],
        note: 'Для устойчивости к броскам тока используйте двухступенчатое торможение.',
      };
    }
    case 'distance': {
      const zl = Number(data.zl);
      const u = Number(data.u);
      const length = Number(data.length);
      const zProtected = zl * length;
      const iFault = (u * 1000) / (Math.sqrt(3) * zProtected);
      return {
        title: 'Дистанционная защита',
        metrics: [
          { label: 'Сопротивление зоны', value: `${zProtected.toFixed(2)} Ом` },
          { label: 'Ожидаемый ток КЗ', value: `${iFault.toFixed(1)} A` },
        ],
        note: 'Зона 1 принимается 80% длины линии, зона 2 — 120% для резервирования.',
      };
    }
    case 'fault': {
      const skz = Number(data.skz);
      const u = Number(data.u);
      const ik = (skz * 1e6) / (Math.sqrt(3) * u * 1000);
      const peak = ik * (1 + Number(data.xR));
      return {
        title: 'Расчёт токов КЗ',
        metrics: [
          { label: 'Ток КЗ 3ф', value: `${ik.toFixed(1)} kA` },
          { label: 'Пиковый ток', value: `${peak.toFixed(1)} kA` },
        ],
        note: 'Сверьте термическую стойкость выключателей и шинопроводов.',
      };
    }
    case 'ctcheck': {
      const classAcc = Number(data.class);
      const isecondary = Number(data.isecondary);
      const burden = Number(data.burden);
      const error = (burden / (isecondary * classAcc)) * 100;
      return {
        title: 'Проверка ТТ',
        metrics: [
          { label: 'Относительная погрешность', value: `${error.toFixed(2)} %` },
          { label: 'Нагрузка цепи', value: `${burden.toFixed(2)} Ом` },
        ],
        note: 'Погрешность не должна превышать 10% для класса 10Р.',
      };
    }
    case 'selectivity': {
      const iprev = Number(data.iprev);
      const ks = Number(data.ks);
      const dt = Number(data.dt);
      const inext = iprev * ks;
      return {
        title: 'Селективность',
        metrics: [
          { label: 'Уставка следующей ступени', value: `${inext.toFixed(1)} A` },
          { label: 'Временной запас', value: `${dt.toFixed(2)} c` },
        ],
        note: 'Соблюдайте не менее 0,2 с между ступенями для надежности отключения.',
      };
    }
    case 'tznp': {
      const ig = Number(data.ig);
      const rz = Number(data.rz);
      const t = Number(data.t);
      const iSetting = ig * 0.6;
      const voltage = iSetting * rz;
      return {
        title: 'ТЗНП',
        metrics: [
          { label: 'Ток срабатывания', value: `${iSetting.toFixed(1)} A` },
          { label: 'Напряжение на реле', value: `${voltage.toFixed(1)} В` },
          { label: 'Время задержки', value: `${t.toFixed(2)} c` },
        ],
        note: 'Учитывайте емкостные токи сети при выборе уставки.',
      };
    }
    case 'stability': {
      const inertia = Number(data.inertia);
      const iosc = Number(data.iosc);
      const ks = Number(data.ks);
      const margin = ks - (iosc / 1000) * inertia;
      return {
        title: 'Стойкость к качаниям',
        metrics: [
          { label: 'Запас устойчивости', value: `${margin.toFixed(2)}` },
          { label: 'Макс. ток качаний', value: `${iosc.toFixed(1)} A` },
        ],
        note: 'Запас устойчивости должен быть > 0,3 для надёжной работы.',
      };
    }
    default:
      return {
        title: 'Результат',
        metrics: [],
        note: 'Нет данных',
      };
  }
};

rzaTabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    setActiveRzaTab(button.dataset.rzaTab);
  });
});

rzaPanels.forEach((panel) => {
  panel.addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const result = calculateRza(form.dataset.rzaPanel, data);
    renderRzaResult(result);
  });
});

rzaExportButtons.forEach((button) => {
  button.addEventListener('click', () => {
    if (!rzaResultsContainer || !rzaResultsContainer.children.length) {
      alert('Нет рассчитанных данных для экспорта');
      return;
    }
    button.textContent = `${button.dataset.rzaExport === 'pdf' ? 'PDF' : 'Excel'} готов`;
    setTimeout(() => {
      button.textContent = button.dataset.rzaExport === 'pdf' ? 'Экспорт PDF' : 'Экспорт Excel';
    }, 1200);
  });
});

if (rzaSubstationSelect) {
  renderSubstationInfo(rzaSubstationSelect.value);
  rzaSubstationSelect.addEventListener('change', (event) => {
    renderSubstationInfo(event.target.value);
  });
}

setActiveRzaTab('mtz');
