class Carousel {
    constructor(controller) {
        this.controller = controller;
        const targetId = controller.getAttribute("for");
        this.container = document.getElementById(targetId);
        if (!this.container) return;

        this.container.classList.add("carousel-target");
        this.index = 0;

        // make first item active if none
        const items = this.getItems();
        if (items.length && !items.some(i => i.classList.contains("active"))) {
            items[0].classList.add("active");
        }

        this.index = items.length-1

        this.createControls();
        this.update(); // force initial height set
        this.observeChanges();
    }

    getItems() {
        return Array.from(this.container.children);
    }

    update() {
        const items = this.getItems();
        if (!items.length) return;

        items.forEach((el, i) => {
            el.classList.toggle("active", i === this.index);
        });

        // set container height to active item
        const active = items[this.index];
        if (active) {
            this.container.style.height = active.offsetHeight + "px";
        }
    }

    next() {
        const items = this.getItems();
        this.index = (this.index + 1) % items.length;
        this.update();
    }

    prev() {
        const items = this.getItems();
        this.index = (this.index - 1 + items.length) % items.length;
        this.update();
    }

    focusNewest() {
        const items = this.getItems();
        if (!items.length) return;
        this.index = items.length - 1;
        this.update();
    }

    createControls() {
        const prevBtn = document.createElement("button");
        prevBtn.textContent = "←";
        prevBtn.onclick = () => this.prev();

        const nextBtn = document.createElement("button");
        nextBtn.textContent = "→";
        nextBtn.onclick = () => this.next();

        this.controller.appendChild(prevBtn);
        this.controller.appendChild(nextBtn);
    }

    observeChanges() {
        const observer = new MutationObserver(() => this.focusNewest());
        observer.observe(this.container, { childList: true });
    }
}

function initCarousels() {
    document.querySelectorAll(".carousel:not([data-init])").forEach(el => {
        el.dataset.init = "true";
        new Carousel(el);
    });
}

document.addEventListener("DOMContentLoaded", initCarousels);
new MutationObserver(() => initCarousels())
    .observe(document.body, { childList: true, subtree: true });