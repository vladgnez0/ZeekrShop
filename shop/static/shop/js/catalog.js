(() => {
  const slider = document.getElementById('priceSlider');
  if (!slider) return;
  // Если пользователь двигает ползунок — ставим значение в поле max
  slider.addEventListener('input', () => {
    const form = slider.closest('form');
    if (!form) return;
    const maxInput = form.querySelector('input[name="max"]');
    if (maxInput) maxInput.value = slider.value;
  });
})();
