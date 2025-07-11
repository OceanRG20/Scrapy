const products = [
  { name: "Laptop", price: "$799" },
  { name: "Smartphone", price: "$499" },
  { name: "Headphones", price: "$99" },
  { name: "Keyboard", price: "$49" },
];

const list = document.getElementById("product-list");

products.forEach((product) => {
  const li = document.createElement("li");
  li.className = "product-item";
  li.innerHTML = `
    <span class="product-name">${product.name}</span> - 
    <span class="product-price">${product.price}</span>
  `;
  list.appendChild(li);
});
