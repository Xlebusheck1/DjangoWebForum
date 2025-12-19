document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("header-search-input");
  const container = document.getElementById("questions-container");
  if (!input || !container) return;

  let timer = null;

  const originalContent = container.innerHTML;

  input.addEventListener("input", () => {
    const q = input.value.trim();
    clearTimeout(timer);

    if (!q) {      
      container.innerHTML = originalContent;
      return;
    }

    timer = setTimeout(() => {
      const params = new URLSearchParams();
      params.set("q", q);

      fetch(`/api/search-order/?${params.toString()}`)
        .then((res) => res.json())
        .then((data) => {
          const order = data.order || [];
          if (!order.length) return;

          const cards = Array.from(
            container.querySelectorAll(".question[data-question-id]")
          );

          const mapById = new Map();
          cards.forEach((card) => {
            mapById.set(card.dataset.questionId, card);
          });

          const fragment = document.createDocumentFragment();

          order.forEach((id) => {
            const el = mapById.get(String(id));
            if (el) fragment.appendChild(el);
          });

          cards.forEach((card) => {
            if (!order.includes(Number(card.dataset.questionId))) {
              fragment.appendChild(card);
            }
          });

          container.innerHTML = "";
          container.appendChild(fragment);
        })
        .catch(() => {});
    }, 300);
  });
});