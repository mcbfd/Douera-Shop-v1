// Logique d'animation au défilement (Scroll-Triggered Storytelling)

document.addEventListener('DOMContentLoaded', () => {
  // Elements à animer
  const animatedElements = document.querySelectorAll('.fade-in, .slide-in-right, .slide-in-bottom');

  // Options pour l'Intersection Observer
  const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.15 // 15% de l'élément doit être visible pour déclencher l'animation
  };

  // Callback de l'observer
  const observerCallback = (entries, observer) => {
      entries.forEach(entry => {
          if (entry.isIntersecting) {
              // Ajouter la classe 'is-visible' pour déclencher la transition CSS
              entry.target.classList.add('is-visible');
              
              // Optionnel : on peut arrêter d'observer une fois l'animation déclenchée
              observer.unobserve(entry.target);
          }
      });
  };

  // Création de l'observer
  const scrollObserver = new IntersectionObserver(observerCallback, observerOptions);

  // Observer chaque élément
  animatedElements.forEach(element => {
      scrollObserver.observe(element);
  });

  // Gestion du smooth scrolling pour les ancres de navigation
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
          e.preventDefault();
          
          const targetId = this.getAttribute('href');
          if(targetId === "#") return;
          
          const targetElement = document.querySelector(targetId);
          if (targetElement) {
              targetElement.scrollIntoView({
                  behavior: 'smooth'
              });
          }
      });
  });

  // Modal Logique
  const modal = document.getElementById('starter-kit-modal');
  const openBtn = document.getElementById('open-kit-btn');
  const closeBtn = document.querySelector('.close-modal');

  if (openBtn && modal) {
      openBtn.addEventListener('click', (e) => {
          e.preventDefault();
          modal.style.display = 'flex';
          // Petite pause pour permettre l'apparition de l'animation CSS
          setTimeout(() => {
              modal.classList.add('show');
          }, 10);
      });

      const closeModal = () => {
          modal.classList.remove('show');
          setTimeout(() => {
              modal.style.display = 'none';
          }, 300); // Correspond à la durée de la transition CSS
      };

      closeBtn.addEventListener('click', closeModal);

      // Fermer au clic hors du contenu
      window.addEventListener('click', (e) => {
          if (e.target === modal) {
              closeModal();
          }
      });
  }
});
