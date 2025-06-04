// Create animated stars
function createStars() {
    const starsContainer = document.getElementById('stars');
    const numberOfStars = 50;

    for (let i = 0; i < numberOfStars; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.width = Math.random() * 3 + 1 + 'px';
        star.style.height = star.style.width;
        star.style.animationDelay = Math.random() * 2 + 's';
        starsContainer.appendChild(star);
    }
}

// Animate the 404 number on click
function animate404() {
    const errorCode = document.getElementById('errorCode');
    errorCode.style.transform = 'scale(1.1) rotate(5deg)';
    errorCode.style.transition = 'transform 0.3s ease';

    setTimeout(() => {
        errorCode.style.transform = 'scale(1) rotate(0deg)';
    }, 300);
}

// Handle navigation buttons
function setupNavigation() {
    const backBtn = document.getElementById('backBtn');
    const randomBtn = document.getElementById('randomBtn');
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');

    backBtn.addEventListener('click', () => {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    });

    randomBtn.addEventListener('click', () => {
        const randomPages = [
            '/about',
            '/contact',
            '/services',
            '/blog',
            '/portfolio',
            '/team'
        ];
        const randomPage = randomPages[Math.floor(Math.random() * randomPages.length)];
        window.location.href = randomPage;
    });

    // Search functionality
    function performSearch() {
        const query = searchInput.value.trim();
        if (query) {
            // You can customize this to redirect to your search page
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    }

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Add click effect to 404
document.getElementById('errorCode').addEventListener('click', animate404);

// Mouse movement parallax effect
document.addEventListener('mousemove', (e) => {
    const mouseX = e.clientX / window.innerWidth;
    const mouseY = e.clientY / window.innerHeight;

    const floatingElements = document.querySelectorAll('.floating-element');
    floatingElements.forEach((element, index) => {
        const speed = (index + 1) * 0.5;
        const x = (mouseX - 0.5) * speed * 20;
        const y = (mouseY - 0.5) * speed * 20;
        element.style.transform = `translate(${x}px, ${y}px)`;
    });
});

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', () => {
    createStars();
    setupNavigation();

    // Add a subtle page load animation
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

// Add some keyboard shortcuts
document.addEventListener('keydown', (e) => {
    switch(e.key) {
        case 'h':
        case 'H':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                window.location.href = '/';
            }
            break;
        case 'Escape':
            window.history.back();
            break;
    }
});
