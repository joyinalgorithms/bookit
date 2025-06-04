document.addEventListener("DOMContentLoaded", () => {
    const menuIcon = document.querySelector(".iconmenu");
    const sidebar = document.querySelector(".sidebar");
    const bodyContent = document.querySelector(".body-content");
    const bodyHeader = document.querySelector(".body-header");

    menuIcon.addEventListener("click", () => {
        const isClosed = sidebar.classList.toggle("closed");
        bodyContent.classList.toggle("expanded", isClosed);
        bodyHeader.classList.toggle("expanded", isClosed);
    });
});
