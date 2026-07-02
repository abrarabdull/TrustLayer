document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const closeBtn = alert.querySelector('.btn-close');
      if (closeBtn) {
        closeBtn.click();
      }
    }, 6000);
  });
});
