'use strict';

(() => {
  const screens = {
    tree: {
      src: 'images/tree-build-ru.png',
      caption: 'Выбранные пассивки и характеристики готового билда',
      alt: 'Готовый билд с деревом 0_4 в русской Path of Building 2: выбранные пассивки и характеристики персонажа слева'
    },
    import: {
      src: 'images/import-ru.jpg',
      caption: 'Обычные коды PoB и импорт своего персонажа',
      alt: 'Окно импорта персонажа и обмена билдами в русской Path of Building 2'
    },
    trade: {
      src: 'images/trade-compare.png',
      caption: 'Примерка найденного самострела и сравнение характеристик',
      alt: 'Реальный пример торгового поиска: самострел и изменения характеристик при его экипировке'
    }
  };
  const tabs = document.querySelector('.gallery-tabs');
  const buttons = [...tabs.querySelectorAll('button[data-screen]')];
  const image = document.getElementById('screen-image');
  const link = document.getElementById('screen-link');
  const caption = document.getElementById('screen-caption');
  const dialog = document.getElementById('screen-dialog');
  const dialogImage = document.getElementById('dialog-image');
  const dialogCaption = document.getElementById('dialog-caption');
  const closeButton = document.getElementById('close-dialog');
  let selected = 'tree';

  function selectScreen(key) {
    const screen = screens[key];
    if (!screen) return;
    selected = key;
    image.src = screen.src;
    image.alt = screen.alt;
    link.href = screen.src;
    link.setAttribute('aria-label', 'Увеличить скриншот: ' + screen.caption);
    caption.textContent = screen.caption;
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.screen === key)));
  }

  buttons.forEach(button => button.addEventListener('click', () => selectScreen(button.dataset.screen)));
  tabs.hidden = false;

  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    const screen = screens[selected];
    dialogImage.src = screen.src;
    dialogImage.alt = screen.alt;
    dialogCaption.textContent = screen.caption;
    dialog.showModal();
    document.body.style.overflow = 'hidden';
  });
  closeButton.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => { document.body.style.overflow = ''; });
})();
