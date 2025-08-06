document.addEventListener("DOMContentLoaded", function () {
    const activeCategory = document.querySelector(".menu-scroll-container .menu-category.active");
    if (activeCategory) {
      activeCategory.scrollIntoView({ inline: "center", behavior: "smooth", block: "nearest" });
    }
  });
