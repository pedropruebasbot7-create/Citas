document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.querySelector('input[type="date"]');
  if (dateInput) {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    dateInput.min = `${yyyy}-${mm}-${dd}`;
  }

  document.querySelectorAll('.add-cart').forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.dataset.id;
      const nombre = button.dataset.nombre || 'Producto';
      const precio = Number(button.dataset.precio || 0);
      const cart = JSON.parse(localStorage.getItem('umbra_cart') || '[]');
      const item = cart.find((entry) => entry.id === id);
      if (item) {
        item.cantidad += 1;
      } else {
        cart.push({ id, nombre, precio, cantidad: 1 });
      }
      localStorage.setItem('umbra_cart', JSON.stringify(cart));
      button.textContent = 'Añadido';
      setTimeout(() => {
        button.textContent = '+ Añadir';
      }, 800);
    });
  });
});
