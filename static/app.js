const state = {
  collection: null,
  course: {course: {}, collections: []},
  history: [],
  activeMaterial: null,
  scrollPositions: new Map(),
  readerSettings: {fontSize: 'medium', lineHeight: 'comfortable'}
};

const main = document.querySelector('main');
const workspace = document.querySelector('#workspace');
const materials = document.querySelector('#materials');
const messages = document.querySelector('#messages');
const welcome = document.querySelector('#welcome');
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const send = document.querySelector('#send');
const collectionSelect = document.querySelector('#collection-select');
const reader = document.querySelector('#reader');
const readerTitle = document.querySelector('#reader-title');
const readerMeta = document.querySelector('#reader-meta');
const readerBody = document.querySelector('#reader-body');
const readerScroll = document.querySelector('#reader-scroll');
const readerClose = document.querySelector('#reader-close');
const readerBack = document.querySelector('#reader-back');
const readerTop = document.querySelector('#reader-top');
const readerProgress = document.querySelector('#reader-progress-bar');
const readerToc = document.querySelector('#reader-toc');
const tocToggle = document.querySelector('#toc-toggle');
const typeToggle = document.querySelector('#type-toggle');
const typePanel = document.querySelector('#type-panel');
const pdfFrame = document.querySelector('#pdf-frame');
const pdfOpen = document.querySelector('#pdf-open');
const tutorPanel = document.querySelector('#tutor-panel');
const tutorToggle = document.querySelector('#tutor-toggle');
const tutorClose = document.querySelector('#tutor-close');
const tutorContext = document.querySelector('#tutor-context');
const libraryToggle = document.querySelector('#library-toggle');

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function activeCollection() {
  return state.course.collections.find(item => item.id === state.collection) || {items: []};
}

function renderTabs() {
  collectionSelect.replaceChildren();
  state.course.collections.forEach(item => {
    const option = make('option', '', item.title);
    option.value = item.id;
    option.selected = item.id === state.collection;
    collectionSelect.append(option);
  });
  collectionSelect.onchange = () => {
    state.collection = collectionSelect.value;
    renderMaterials();
  };
}

function renderMaterials() {
  materials.replaceChildren();
  activeCollection().items.forEach(item => {
    const button = make('button', 'material');
    button.type = 'button';
    const displayFile = item.display_file || item.file;
    button.dataset.file = `/materials/${encodeURI(displayFile)}`;
    button.dataset.materialId = item.id;
    button.append(make('strong', '', item.title), make('small', '', displayFile.split('/').pop()));
    if (state.activeMaterial?.id === item.id) button.classList.add('active');
    button.onclick = () => openMaterial(item, button);
    materials.appendChild(button);
  });
}

function renderInline(parent, text) {
  const pattern = /(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^)\n]+\))/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    parent.append(document.createTextNode(text.slice(cursor, match.index)));
    const token = match[0];
    if (token.startsWith('`')) {
      parent.append(make('code', '', token.slice(1, -1)));
    } else if (token.startsWith('**')) {
      parent.append(make('strong', '', token.slice(2, -2)));
    } else if (token.startsWith('*')) {
      parent.append(make('em', '', token.slice(1, -1)));
    } else {
      const parts = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      let safeUrl = null;
      try {
        const parsed = new URL(parts[2], window.location.href);
        if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) safeUrl = parsed.href;
      } catch (_) {
        safeUrl = null;
      }
      if (safeUrl) {
        const link = make('a', '', parts[1]);
        link.href = safeUrl;
        if (safeUrl.startsWith('http')) {
          link.target = '_blank';
          link.rel = 'noreferrer';
        }
        parent.append(link);
      } else {
        parent.append(document.createTextNode(parts[1]));
      }
    }
    cursor = match.index + token.length;
  }
  parent.append(document.createTextNode(text.slice(cursor)));
}

function headingId(text, usedIds) {
  const base = text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '') || 'section';
  let id = base;
  let suffix = 2;
  while (usedIds.has(id)) id = `${base}-${suffix++}`;
  usedIds.add(id);
  return id;
}

function tableCells(line) {
  return line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
}

function isTableDivider(line) {
  const cells = tableCells(line);
  return cells.length > 0 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
}

function renderMarkdownPage(text, container, tocEntries, usedIds, skipFirstHeading) {
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  let index = 0;
  let firstHeadingSkipped = !skipFirstHeading;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const fence = line.match(/^\s*(```+|~~~+)\s*([\w-]*)\s*$/);
    if (fence) {
      const code = [];
      index += 1;
      while (index < lines.length && !new RegExp(`^\\s*${fence[1][0]}{${fence[1].length},}\\s*$`).test(lines[index])) {
        code.push(lines[index++]);
      }
      if (index < lines.length) index += 1;
      const pre = make('pre');
      const codeNode = make('code', '', code.join('\n'));
      if (fence[2]) codeNode.dataset.language = fence[2];
      pre.append(codeNode);
      container.append(pre);
      continue;
    }

    if (line.includes('|') && index + 1 < lines.length && isTableDivider(lines[index + 1])) {
      const table = make('table');
      const thead = make('thead');
      const headRow = make('tr');
      tableCells(line).forEach(cell => {
        const th = make('th');
        renderInline(th, cell);
        headRow.append(th);
      });
      thead.append(headRow);
      table.append(thead);
      index += 2;
      const tbody = make('tbody');
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        const row = make('tr');
        tableCells(lines[index]).forEach(cell => {
          const td = make('td');
          renderInline(td, cell);
          row.append(td);
        });
        tbody.append(row);
        index += 1;
      }
      table.append(tbody);
      container.append(table);
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+?)\s*#*$/);
    if (heading) {
      const level = Math.min(4, heading[1].length);
      const textContent = heading[2].trim();
      index += 1;
      if (!firstHeadingSkipped && level === 1) {
        firstHeadingSkipped = true;
        continue;
      }
      const displayLevel = level === 1 ? 2 : level;
      const node = make(`h${displayLevel}`);
      const id = headingId(textContent, usedIds);
      node.id = id;
      renderInline(node, textContent);
      container.append(node);
      tocEntries.push({id, text: textContent, level: displayLevel});
      continue;
    }

    if (/^\s*(?:[-*_]\s*){3,}$/.test(line)) {
      container.append(make('hr'));
      index += 1;
      continue;
    }

    const listMatch = line.match(/^\s*([-+*]|\d+\.)\s+(.+)$/);
    if (listMatch) {
      const ordered = /\d+\./.test(listMatch[1]);
      const list = make(ordered ? 'ol' : 'ul');
      while (index < lines.length) {
        const item = lines[index].match(/^\s*([-+*]|\d+\.)\s+(.+)$/);
        if (!item || /\d+\./.test(item[1]) !== ordered) break;
        const li = make('li');
        renderInline(li, item[2]);
        list.append(li);
        index += 1;
      }
      container.append(list);
      continue;
    }

    if (/^\s*>/.test(line)) {
      const quoteLines = [];
      while (index < lines.length && /^\s*>/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^\s*>\s?/, ''));
        index += 1;
      }
      const quote = make('blockquote');
      renderInline(quote, quoteLines.join(' '));
      container.append(quote);
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;
    while (index < lines.length && lines[index].trim()) {
      const next = lines[index];
      if (/^(#{1,4})\s+/.test(next) || /^\s*(```+|~~~+)/.test(next) || /^\s*([-+*]|\d+\.)\s+/.test(next) || /^\s*>/.test(next)) break;
      if (next.includes('|') && index + 1 < lines.length && isTableDivider(lines[index + 1])) break;
      paragraphLines.push(next.trim());
      index += 1;
    }
    const paragraph = make('p');
    renderInline(paragraph, paragraphLines.join(' '));
    container.append(paragraph);
  }
}

function renderToc(entries) {
  readerToc.replaceChildren(make('p', 'toc-title', 'Contents'));
  if (!entries.length) {
    readerToc.append(make('p', 'toc-empty', 'This document has no section headings.'));
    tocToggle.disabled = true;
    return;
  }
  tocToggle.disabled = false;
  entries.forEach(entry => {
    const button = make('button', `toc-link level-${entry.level}`, entry.text);
    button.type = 'button';
    button.onclick = () => {
      document.getElementById(entry.id)?.scrollIntoView({behavior: 'smooth', block: 'start'});
      if (window.innerWidth <= 760) toggleToc(false);
    };
    readerToc.append(button);
  });
}

function renderDocument(text, item) {
  const pages = text.split('\f').map(page => page.trim()).filter(Boolean);
  readerBody.replaceChildren();
  readerBody.lang = state.course.course?.language || 'en';

  const header = make('header', 'document-header');
  header.append(make('p', 'document-kicker', activeCollection().title || 'Course material'));
  header.append(make('h1', 'document-title', item.title));
  readerBody.append(header);

  if (!pages.length) {
    readerBody.append(make('div', 'reader-empty', 'No readable content.'));
    renderToc([]);
    return;
  }

  const tocEntries = [];
  const usedIds = new Set();
  pages.forEach((page, pageIndex) => {
    const section = make('section', 'reader-page');
    if (pages.length > 1) section.append(make('p', 'reader-page-number', `PAGE ${pageIndex + 1} OF ${pages.length}`));
    renderMarkdownPage(page, section, tocEntries, usedIds, pageIndex === 0);
    readerBody.append(section);
  });
  renderToc(tocEntries);
}

function loadingState() {
  const wrap = make('div', 'reader-skeleton');
  for (let i = 0; i < 6; i += 1) wrap.append(make('span'));
  readerBody.replaceChildren(wrap);
  readerToc.replaceChildren();
}

function saveReadingPosition() {
  if (state.activeMaterial) state.scrollPositions.set(state.activeMaterial.id, readerScroll.scrollTop);
}

async function openMaterial(item, button) {
  saveReadingPosition();
  materials.querySelectorAll('.material.active').forEach(element => element.classList.remove('active'));
  button.classList.add('active');
  state.activeMaterial = item;
  const displayFile = item.display_file || item.file;
  const isPdf = displayFile.toLowerCase().endsWith('.pdf');
  readerTitle.textContent = item.title;
  readerMeta.textContent = `${activeCollection().title} · ${displayFile}`;
  tutorContext.textContent = item.title;
  document.body.classList.add('reading-active');
  workspace.classList.add('reading');
  workspace.classList.toggle('pdf-reading', isPdf);
  reader.classList.toggle('pdf-mode', isPdf);
  pdfOpen.hidden = !isPdf;
  main.classList.remove('show-materials');
  toggleToc(false);
  typePanel.hidden = true;
  typeToggle.classList.remove('active');
  typeToggle.setAttribute('aria-expanded', 'false');
  loadingState();
  readerScroll.scrollTop = 0;
  updateReaderProgress();

  try {
    if (isPdf) {
      const response = await fetch(button.dataset.file, {method: 'HEAD'});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      pdfFrame.title = item.title;
      pdfFrame.src = `${button.dataset.file}#view=FitH&toolbar=1&navpanes=0`;
      return;
    }
    pdfFrame.src = 'about:blank';
    const response = await fetch(button.dataset.file);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderDocument(await response.text(), item);
    applyReaderSettings();
    requestAnimationFrame(() => {
      readerScroll.scrollTop = state.scrollPositions.get(item.id) || 0;
      updateReaderProgress();
      readerScroll.focus({preventScroll: true});
    });
  } catch (error) {
    workspace.classList.remove('pdf-reading');
    reader.classList.remove('pdf-mode');
    pdfOpen.hidden = true;
    const errorState = make('div', 'reader-empty reader-error');
    errorState.append(make('p', '', `Failed to load ${item.title}: ${error.message}`));
    const retry = make('button', 'toolbar-button', 'Retry');
    retry.type = 'button';
    retry.onclick = () => openMaterial(item, button);
    errorState.append(retry);
    readerBody.replaceChildren(errorState);
    renderToc([]);
  }
}

function closeReader({showMaterials = false} = {}) {
  saveReadingPosition();
  document.body.classList.remove('reading-active');
  workspace.classList.remove('reading', 'tutor-open', 'pdf-reading');
  tutorToggle.setAttribute('aria-expanded', 'false');
  materials.querySelectorAll('.material.active').forEach(element => element.classList.remove('active'));
  if (showMaterials && window.innerWidth <= 760) main.classList.add('show-materials');
  if (messages.children.length && !showMaterials) workspace.classList.add('chatting');
  else workspace.classList.remove('chatting');
}

function preserveReadingAnchor(changeLayout) {
  if (!workspace.classList.contains('reading')) {
    changeLayout();
    return;
  }
  const scrollTop = readerScroll.getBoundingClientRect().top;
  const candidates = readerBody.querySelectorAll('h1, h2, h3, h4, p, li, pre, table, blockquote');
  let anchor = null;
  for (const candidate of candidates) {
    if (candidate.getBoundingClientRect().top <= scrollTop + 12) anchor = candidate;
    else break;
  }
  const offset = anchor ? anchor.getBoundingClientRect().top - scrollTop : 0;
  changeLayout();
  requestAnimationFrame(() => {
    if (anchor) readerScroll.scrollTop += anchor.getBoundingClientRect().top - scrollTop - offset;
    updateReaderProgress();
  });
}

function openTutor() {
  preserveReadingAnchor(() => {
    workspace.classList.add('chatting');
    if (workspace.classList.contains('reading')) workspace.classList.add('tutor-open');
  });
  tutorToggle.setAttribute('aria-expanded', 'true');
  input.focus();
}

function closeTutor() {
  preserveReadingAnchor(() => workspace.classList.remove('tutor-open'));
  tutorToggle.setAttribute('aria-expanded', 'false');
  if (!workspace.classList.contains('reading')) workspace.classList.remove('chatting');
}

function tutorIsOpen() {
  return workspace.classList.contains('reading')
    ? workspace.classList.contains('tutor-open')
    : workspace.classList.contains('chatting');
}

function toggleTutor() {
  if (tutorIsOpen()) closeTutor();
  else openTutor();
}

function handleTutorShortcut(event) {
  if (event.ctrlKey && !event.altKey && !event.metaKey && event.code === 'Backquote') {
    event.preventDefault();
    event.stopPropagation();
    toggleTutor();
    return true;
  }
  return false;
}

function bindPdfShortcut() {
  try {
    pdfFrame.contentWindow?.addEventListener('keydown', handleTutorShortcut, true);
  } catch (_) {
    // Native PDF viewers may isolate their internal document.
  }
}

function toggleToc(force) {
  const open = force ?? !readerToc.classList.contains('open');
  readerToc.classList.toggle('open', open);
  tocToggle.classList.toggle('active', open);
  tocToggle.setAttribute('aria-expanded', String(open));
}

function applyReaderSettings() {
  readerBody.classList.toggle('text-small', state.readerSettings.fontSize === 'small');
  readerBody.classList.toggle('text-large', state.readerSettings.fontSize === 'large');
  readerBody.classList.toggle('leading-compact', state.readerSettings.lineHeight === 'compact');
  readerBody.classList.toggle('leading-spacious', state.readerSettings.lineHeight === 'spacious');
  document.querySelectorAll('[data-font-size]').forEach(button => button.classList.toggle('active', button.dataset.fontSize === state.readerSettings.fontSize));
  document.querySelectorAll('[data-line-height]').forEach(button => button.classList.toggle('active', button.dataset.lineHeight === state.readerSettings.lineHeight));
  try { localStorage.setItem('courseweaver-reader-settings', JSON.stringify(state.readerSettings)); } catch (_) {}
  updateReaderProgress();
}

function updateReaderProgress() {
  const range = readerScroll.scrollHeight - readerScroll.clientHeight;
  const progress = range > 0 ? Math.min(100, (readerScroll.scrollTop / range) * 100) : 0;
  readerProgress.style.width = `${progress}%`;
  readerTop.classList.toggle('visible', readerScroll.scrollTop > 480);
}

function addMessage(role, text, sources = []) {
  openTutor();
  const item = make('article', `message ${role}`, text);
  if (sources.length) {
    const source = make('div', 'sources', `Sources: ${sources.map(entry => `${entry.id} p.${entry.page}`).join(' · ')}`);
    item.append(source);
  }
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

async function ask(text) {
  addMessage('user', text);
  input.value = '';
  send.disabled = true;
  const waiting = addMessage('assistant', 'Searching course materials...');
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, history: state.history})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    waiting.remove();
    addMessage('assistant', data.answer, data.sources || []);
    state.history.push({role: 'user', content: text}, {role: 'assistant', content: data.answer});
  } catch (error) {
    waiting.textContent = error.message;
    waiting.classList.add('error');
  } finally {
    send.disabled = false;
    input.focus();
  }
}

readerClose.onclick = () => closeReader();
readerBack.onclick = () => closeReader({showMaterials: true});
tutorToggle.onclick = toggleTutor;
tutorClose.onclick = closeTutor;
tocToggle.onclick = () => toggleToc();
typeToggle.onclick = () => {
  typePanel.hidden = !typePanel.hidden;
  typeToggle.classList.toggle('active', !typePanel.hidden);
  typeToggle.setAttribute('aria-expanded', String(!typePanel.hidden));
};
pdfOpen.onclick = () => {
  if (state.activeMaterial) {
    const displayFile = state.activeMaterial.display_file || state.activeMaterial.file;
    window.open(`/materials/${encodeURI(displayFile)}`, '_blank', 'noopener');
  }
};
pdfFrame.addEventListener('load', bindPdfShortcut);
libraryToggle.onclick = () => main.classList.toggle('show-materials');
readerTop.onclick = () => readerScroll.scrollTo({top: 0, behavior: 'smooth'});
readerScroll.addEventListener('scroll', updateReaderProgress, {passive: true});
window.addEventListener('beforeunload', saveReadingPosition);

document.addEventListener('keydown', handleTutorShortcut, true);

document.addEventListener('click', event => {
  if (!typePanel.hidden && !typePanel.contains(event.target) && !typeToggle.contains(event.target)) {
    typePanel.hidden = true;
    typeToggle.classList.remove('active');
    typeToggle.setAttribute('aria-expanded', 'false');
  }
});

document.querySelectorAll('[data-font-size]').forEach(button => {
  button.onclick = () => {
    state.readerSettings.fontSize = button.dataset.fontSize;
    applyReaderSettings();
  };
});
document.querySelectorAll('[data-line-height]').forEach(button => {
  button.onclick = () => {
    state.readerSettings.lineHeight = button.dataset.lineHeight;
    applyReaderSettings();
  };
});

document.querySelectorAll('[data-prompt]').forEach(button => button.onclick = () => ask(button.dataset.prompt));
form.onsubmit = event => {
  event.preventDefault();
  const text = input.value.trim();
  if (text) ask(text);
};
input.onkeydown = event => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
};

try {
  const savedSettings = JSON.parse(localStorage.getItem('courseweaver-reader-settings'));
  if (savedSettings?.fontSize) state.readerSettings.fontSize = savedSettings.fontSize;
  if (savedSettings?.lineHeight) state.readerSettings.lineHeight = savedSettings.lineHeight;
} catch (_) {}
applyReaderSettings();

Promise.all([
  fetch('/api/course').then(response => response.json()),
  fetch('/api/status').then(response => response.json())
]).then(([course, status]) => {
  state.course = course;
  state.collection = course.collections?.[0]?.id || null;
  renderTabs();
  renderMaterials();
  document.querySelector('#course-title').textContent = course.course?.title || 'Study Desk';
  document.querySelector('#course-subtitle').textContent = (course.course?.subtitle || 'Course-grounded learning').toUpperCase();
  const itemCount = (course.collections || []).reduce((sum, item) => sum + item.items.length, 0);
  document.querySelector('#status').textContent = `${itemCount} items · ${status.model || status.provider}${status.agent_configured ? '' : ' · configure agent'}`;
});
