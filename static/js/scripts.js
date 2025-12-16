// static/js/scripts.js

document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const groupSelect = document.getElementById('group');
    const bookSelect = document.getElementById('book');
    const studentInput = document.getElementById('student');
    const studentIdField = document.getElementById('student_id');
    const currentGroupIdField = document.getElementById('current_group_id');
    const studentSuggestions = document.getElementById('student-suggestions');
    const quantityInput = document.getElementById('quantity');
    
    // 1. Загружаем группы при загрузке страницы
    loadGroups();
    
    // 2. При выборе группы
    if (groupSelect) {
        groupSelect.addEventListener('change', function() {
            const groupId = this.value;
            currentGroupIdField.value = groupId; // Сохраняем ID группы
            
            if (groupId) {
                loadBooks(groupId);
                studentInput.value = ''; // Очищаем поле
                studentIdField.value = ''; // Очищаем скрытое поле
            } else {
                // Если группа не выбрана
                bookSelect.innerHTML = '<option value="">-- Сначала выберите группу --</option>';
                studentSuggestions.style.display = 'none';
                studentSuggestions.innerHTML = '';
                currentGroupIdField.value = '';
            }
        });
    }
    
    // 3. Поиск студентов при вводе текста (одна буква и более)
    if (studentInput) {
        let searchTimeout;
        
        studentInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            const groupId = currentGroupIdField.value;
            
            // Если группа не выбрана - показываем сообщение
            if (!groupId) {
                showMessage('Сначала выберите группу');
                return;
            }
            
            // Если поле пустое - показываем всех студентов группы
            if (query === '') {
                loadAllStudents(groupId);
                return;
            }
            
            // Ждем 200мс после окончания ввода
            searchTimeout = setTimeout(() => {
                searchStudents(query, groupId);
            }, 200);
        });
        
        // Скрыть подсказки при клике вне поля
        document.addEventListener('click', function(e) {
            if (!studentInput.contains(e.target) && !studentSuggestions.contains(e.target)) {
                studentSuggestions.style.display = 'none';
            }
        });
    }
    
    // Показывать студентов при клике на поле (ВСЕГДА показываем список)
    if (studentInput) {
        studentInput.addEventListener('click', function() {
            const groupId = currentGroupIdField.value;
            
            if (!groupId) {
                showMessage('Сначала выберите группу');
                return;
            }
            
            // ВСЕГДА показываем всех студентов при клике
            loadAllStudents(groupId);
        });
    }


    // 4. Кнопки для количества
    if (quantityInput) {
        const quantityContainer = quantityInput.parentNode;
        
        // Создаем кнопки
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group btn-group-sm mt-2';
        buttonGroup.innerHTML = `
            <button type="button" class="btn btn-outline-secondary" id="decrease-btn">-1</button>
            <button type="button" class="btn btn-outline-secondary" id="increase-btn">+1</button>
        `;
        
        quantityContainer.appendChild(buttonGroup);
        
        // Обработчики кнопок
        document.getElementById('decrease-btn').addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        });
        
        document.getElementById('increase-btn').addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            quantityInput.value = value + 1;
        });
    }
    
    // Функция загрузки групп
    function loadGroups() {
        fetch('/get-groups')
            .then(response => response.json())
            .then(groups => {
                groupSelect.innerHTML = '<option value="">-- Выберите группу --</option>';
                
                groups.forEach(group => {
                    const option = document.createElement('option');
                    option.value = group.id;
                    option.textContent = group.name;
                    groupSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Ошибка загрузки групп:', error);
                groupSelect.innerHTML = '<option value="">Ошибка загрузки групп</option>';
            });
    }
    
    // Функция загрузки книг для группы
    function loadBooks(groupId) {
        fetch(`/get-books/${groupId}`)
            .then(response => response.json())
            .then(books => {
                bookSelect.innerHTML = '<option value="">-- Выберите книгу --</option>';
                
                if (books.length === 0) {
                    const option = document.createElement('option');
                    option.value = "";
                    option.textContent = "Нет доступных книг для вашей группы";
                    bookSelect.appendChild(option);
                    return;
                }
                
                books.forEach(book => {
                    const option = document.createElement('option');
                    option.value = book.id;
                    // Формируем строку с диапазоном ID экземпляров,
                    // например: "ID: 105(01-25)"
                    let copiesInfo = '';
                    if (book.copy_start && book.copy_end) {
                        const startStr = String(book.copy_start).padStart(2, '0');
                        const endStr = String(book.copy_end).padStart(2, '0');
                        const rangeStr = (book.copy_start === book.copy_end)
                            ? `${startStr}`
                            : `${startStr}-${endStr}`;
                        // Код книги = её ID в базе (можно заменить на отдельное поле, если нужно)
                        copiesInfo = ` | ID: ${book.id}(${rangeStr})`;
                    }

                    option.textContent = `${book.name} (доступно: ${book.available})${copiesInfo}`;
                    bookSelect.appendChild(option);
                });
                
                // === ДОБАВЛЕНО: Обновление количества при выборе книги ===
                // Удаляем старый обработчик, если был
                bookSelect.onchange = null;
                
                // Добавляем новый обработчик
                bookSelect.addEventListener('change', function() {
                    const selectedOption = this.options[this.selectedIndex];
                    
                    // Обновляем максимальное значение в поле количества
                    if (selectedOption.value) {
                        // Парсим доступное количество из текста опции
                        const match = selectedOption.textContent.match(/доступно:\s*(\d+)/);
                        if (match && quantityInput) {
                            const maxAvailable = parseInt(match[1]);
                            quantityInput.max = maxAvailable;
                            
                            // Если текущее количество больше доступного, уменьшаем его
                            const currentQuantity = parseInt(quantityInput.value) || 1;
                            if (currentQuantity > maxAvailable) {
                                quantityInput.value = maxAvailable;
                            }
                        }
                    }
                });
                // === КОНЕЦ ДОБАВЛЕНИЯ ===
                
            })
            .catch(error => {
                console.error('Ошибка загрузки книг:', error);
                bookSelect.innerHTML = '<option value="">Ошибка загрузки книг</option>';
            });
    }
    
    // Функция загрузки ВСЕХ студентов группы
    function loadAllStudents(groupId) {
        if (!groupId) return;
        
        fetch(`/get-students/${groupId}`)
            .then(response => response.json())
            .then(students => {
                updateStudentSuggestions(students, 'Студенты группы:');
            })
            .catch(error => {
                console.error('Ошибка загрузки студентов:', error);
                showMessage('Ошибка загрузки студентов');
            });
    }
    
    // Функция поиска студентов
    function searchStudents(query, groupId) {
        if (!groupId) {
            showMessage('Сначала выберите группу');
            return;
        }
        
        fetch(`/search-students?q=${encodeURIComponent(query)}&group_id=${groupId}`)
            .then(response => response.json())
            .then(students => {
                updateStudentSuggestions(students, `Результаты поиска "${query}":`);
            })
            .catch(error => {
                console.error('Ошибка поиска студентов:', error);
                showMessage('Ошибка поиска');
            });
    }
    
    // Общая функция обновления списка студентов
    function updateStudentSuggestions(students, title) {
        studentSuggestions.innerHTML = '';
        
        if (students.length === 0) {
            const item = document.createElement('div');
            item.className = 'list-group-item text-muted';
            item.textContent = 'Студенты не найдены';
            studentSuggestions.appendChild(item);
        } else {
            // Добавляем заголовок
            const titleItem = document.createElement('div');
            titleItem.className = 'list-group-item list-group-item-light';
            titleItem.textContent = title;
            studentSuggestions.appendChild(titleItem);
            
            // Добавляем студентов
            students.forEach(student => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = student.name;
                
                item.addEventListener('click', function() {
                    studentInput.value = student.name;
                    studentIdField.value = student.id;
                    item.dataset.studentId = student.id; // ← ДОБАВИТЬ ЭТУ СТРОКУ
                    studentSuggestions.style.display = 'none';
                });
                
                studentSuggestions.appendChild(item);
            });
        }
        
        studentSuggestions.style.display = 'block';
    }
    
    // Функция показа сообщения
    function showMessage(message) {
        studentSuggestions.innerHTML = '';
        const item = document.createElement('div');
        item.className = 'list-group-item list-group-item-warning';
        item.textContent = message;
        studentSuggestions.appendChild(item);
        studentSuggestions.style.display = 'block';
    }

    // Обработка отправки формы
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Проверяем, введено ли ФИО
            // Проверяем, введено ли ФИО
            const studentName = studentInput.value.trim();
            if (!studentName) {
                document.getElementById('error-message').textContent = 'Ошибка: Введите ФИО студента';
                document.getElementById('error-message').style.display = 'block';
                return;
            }

            // Если студент выбран из списка - у него уже есть ID
            // Если введен вручную - нужно найти его ID
            if (!studentIdField.value) {
                // Ищем студента по введенному имени
                const groupId = currentGroupIdField.value;
                if (!groupId) {
                    document.getElementById('error-message').textContent = 'Ошибка: Сначала выберите группу';
                    document.getElementById('error-message').style.display = 'block';
                    return;
                }
                
                // Ищем студента в уже загруженном списке
                const studentItems = studentSuggestions.querySelectorAll('.list-group-item-action');
                let foundStudentId = null;
                
                studentItems.forEach(item => {
                    if (item.textContent === studentName) {
                        // Нашли совпадение в списке
                        const studentId = item.dataset.studentId;
                        if (studentId) {
                            foundStudentId = studentId;
                        }
                    }
                });
                
                if (foundStudentId) {
                    studentIdField.value = foundStudentId;
                } else {
                    document.getElementById('error-message').textContent = 'Ошибка: Студент не найден. Выберите из списка или проверьте ФИО';
                    document.getElementById('error-message').style.display = 'block';
                    return;
                }
            }
            // Показываем индикатор загрузки
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Отправка...';
            submitBtn.disabled = true;
            
            // Скрываем предыдущие сообщения
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('success-message').style.display = 'none';
            
            // Отправляем форму через Fetch API
            fetch('/request-book', {
                method: 'POST',
                body: new FormData(form)
            })
            .then(response => {
                // Получаем и текст, и статус ответа
                return response.text().then(text => {
                    return { ok: response.ok, status: response.status, text: text };
                });
            })
            .then(result => {
                // Проверяем статус ответа
                if (result.ok) {
                    // Показываем модальное окно с номером запроса
                    showSuccessModal(result.text);
                    
                    // Очищаем форму после успешной отправки
                    form.reset();
                    studentIdField.value = '';
                    currentGroupIdField.value = '';
                    studentSuggestions.innerHTML = '';
                    studentSuggestions.style.display = 'none';
                } else {
                    // Показываем ошибку от сервера
                    document.getElementById('error-message').textContent = result.text || `Ошибка ${result.status}`;
                    document.getElementById('error-message').style.display = 'block';
                }
            })
            .catch(error => {
                document.getElementById('error-message').textContent = 'Ошибка отправки: ' + error.message;
                document.getElementById('error-message').style.display = 'block';
            })
            .finally(() => {
                // Восстанавливаем кнопку
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    }
});

// Функция показа модального окна с номером запроса
function showSuccessModal(message) {
    console.log('Показываем успех:', message);
    
    // Ищем ID в сообщении (формат: "Запрос #15 отправлен!")
    const match = message.match(/#(\d+)/); // Ищем #15
    
    if (match) {
        const requestId = match[1]; // 15
        console.log('ID запроса:', requestId);
        
        // Заполняем ID в модальном окне
        const requestIdElement = document.getElementById('requestId');
        if (requestIdElement) {
            requestIdElement.textContent = requestId; // Просто 15
            requestIdElement.dataset.fullNumber = requestId;
        }
        
        // Показываем модальное окно
        const successModalElement = document.getElementById('successModal');
        if (successModalElement) {
            const successModal = new bootstrap.Modal(successModalElement);
            successModal.show();
        }
    } else {
        alert(message);
    }
}

// ========== ДОБАВИТЬ В КОНЕЦ ФАЙЛА ==========

// Кнопка очистки студента
const clearStudentBtn = document.getElementById('clear-student');
if (clearStudentBtn) {
    clearStudentBtn.addEventListener('click', function() {
        studentInput.value = '';
        studentIdField.value = '';
        studentSuggestions.style.display = 'none';
    });
}

// ========== КОНЕЦ ДОБАВЛЕНИЯ ==========