document.addEventListener('DOMContentLoaded', () => {
    const uploadInput = document.getElementById('uploadInput');
    const submitBtn = document.getElementById('submitBtn');
    const statusEl = document.getElementById('status');
    const resultImage = document.getElementById('resultImage');
    const filterCheckboxes = document.querySelectorAll('.filter-cb'); // <-- НАШИ ЧЕКБОКСЫ

    submitBtn.addEventListener('click', async () => {
        const file = uploadInput.files[0];
        if (!file) {
            statusEl.textContent = '❌ Пожалуйста, выберите файл.';
            return;
        }

        submitBtn.disabled = true;
        statusEl.textContent = '🔄 Идет обработка... (модель работает)';
        resultImage.src = ''; 

        const formData = new FormData();
        formData.append('file', file);

        // --- 1. НОВЫЙ КОД: Собираем фильтры ---
        const params = new URLSearchParams();
        filterCheckboxes.forEach(cb => {
            if (cb.checked) {
                // Мы добавляем ?find=Signature&find=stamp&find=qr-code
                params.append('find', cb.value); 
            }
        });
        
        // Собираем финальный URL
        const url = `http://127.0.0.1:8000/inspect/?${params.toString()}`;
        console.log("Отправляем на:", url); // Для отладки
        // --- КОНЕЦ НОВОГО КОДА ---

        try {
            const response = await fetch(url, { // <-- Используем новый URL
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                // Пытаемся прочитать ошибку из JSON
                const errData = await response.json();
                throw new Error(errData.detail || `Ошибка сервера: ${response.statusText}`);
            }

            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);
            resultImage.src = imageUrl;
            statusEl.textContent = '✅ Готово!';

        } catch (error) {
            console.error('Ошибка:', error);
            statusEl.textContent = `❌ Ошибка: ${error.message}`;
        } finally {
            submitBtn.disabled = false;
        }
    });
});