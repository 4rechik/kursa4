document.addEventListener('DOMContentLoaded', function() {
    const taskInput = document.querySelector('input[name="task"]');
    const addButton = document.querySelector('form button[type="submit"]');
    const todoForm = document.querySelector('form');

    if (taskInput && todoForm) {
        taskInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); // Предотвращаем стандартное поведение Enter (обычно отправку формы)
                addButton.click(); // Эмулируем клик по кнопке "Добавить"
            }
        });
    }
});