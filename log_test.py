#!/usr/bin/env python3
"""
Скрипт для логирования тестов mezoni-vision
Работает с standalone-версией (сервер на localhost:8000)
Скриншоты из Twin загружаются через веб-интерфейс, результаты пишутся сюда

Использование:
  1. Запусти mezoni-vision-standalone/mezoni-vision.exe
  2. Запусти этот скрипт: python log_test.py
  3. Следуй инструкциям
"""

import json
import requests
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
LOG_FILE = "test_log.json"
RESULTS_FILE = "test_results.txt"


def check_server():
    """Проверка доступности сервера"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✓ Сервер подключён (режим: {data.get('mode', 'unknown')})")
            return True
    except:
        pass
    print("  ✗ Сервер не отвечает! Запусти mezoni-vision.exe")
    return False


def send_analysis(screenshot_paths):
    """Отправка скриншотов на анализ"""
    files = {}
    for i, path in enumerate(screenshot_paths, 1):
        if path and os.path.exists(path):
            files[f"photo{i}"] = open(path, "rb")

    if not files:
        return None

    try:
        resp = requests.post(f"{BASE_URL}/analyze", files=files, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ✗ Ошибка анализа: {e}")
        return None
    finally:
        for f in files.values():
            f.close()


def save_log(test_data):
    """Сохранение результата в JSON лог"""
    try:
        # Читаем старый лог
        log_data = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
            except:
                log_data = []

        # Добавляем новую запись
        log_data.append(test_data)

        # Пишем обратно
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Сохранено в {LOG_FILE}")
    except Exception as e:
        print(f"  ✗ Ошибка сохранения лога: {e}")


def save_results_txt(test_data):
    """Сохранение в текстовый файл для быстрого просмотра"""
    line = "=" * 60 + "\n"
    entry = f"""{line}
ТЕСТ №{test_data.get('test_num', '?')} | {test_data.get('timestamp', '')}
📍 {test_data.get('location', 'N/A')}
📝 Заметка: {test_data.get('notes', '')}

Результат анализа:
  Всего рядов: {test_data.get('result', {}).get('fill_stats', {}).get('total_rows', 0)}
  Свободно: {test_data.get('result', {}).get('fill_stats', {}).get('green', 0)}
  Средне: {test_data.get('result', {}).get('fill_stats', {}).get('yellow', 0)}
  Полно: {test_data.get('result', {}).get('fill_stats', {}).get('red', 0)}
  Средняя заполненность: {test_data.get('result', {}).get('fill_stats', {}).get('avg_fill_pct', 0)}%

Рекомендация: {test_data.get('result', {}).get('recommend', 'N/A')}

Ручной подсчёт (ожидалось):
  Свободно: {test_data.get('expected_free', 'N/A')} | Средне: {test_data.get('expected_medium', 'N/A')} | Полно: {test_data.get('expected_full', 'N/A')}

Точность: {test_data.get('accuracy_note', 'N/A')}
{line}

"""
    try:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"  ✓ Сохранено в {RESULTS_FILE}")
    except Exception as e:
        print(f"  ✗ Ошибка сохранения результатов: {e}")


def run_test():
    """Основной цикл теста"""
    print("\n" + "=" * 50)
    print("  ТЕСТИРОВАНИЕ MEZONI-VISION")
    print("  Скриншоты из Twin → анализ → лог")
    print("=" * 50)

    # Информация о тесте
    print("\n📝 Информация:")
    test_num = input("  Номер теста (Enter=авто): ").strip()
    if not test_num:
        test_num = str(len(json.load(open(LOG_FILE))) + 1) if os.path.exists(LOG_FILE) else "1"

    location = input(f"  Склад/этаж (например, 'Склад5_Этаж3'): ").strip()
    notes = input(f"  Заметка (например, 'освещение норм'): ").strip()

    # Пути к скриншотам
    print("\n📷 Скриншоты из Twin (полный путь к 4 файлам):")
    print("     Подсказка: можно перетащить файл в окно терминала")
    screenshots = []
    for i in range(1, 5):
        path = input(f"  Секция {i}: ").strip().strip('"')  # Убираем кавычки
        if path:
            if not os.path.exists(path):
                print(f"    ✗ Файл не найден: {path}")
                path = None
            else:
                print(f"    ✓ Принято: {os.path.basename(path)}")
        screenshots.append(path)

    if not any(screenshots):
        print("\n❌ Нет скриншотов! Тест отменён.")
        return

    # Отправка на анализ
    print("\n🔄 Анализ...")
    result = send_analysis(screenshots)

    if not result:
        print("\n❌ Анализ не выполнен!")
        return

    # Вывод результата
    print("\n" + "=" * 50)
    print("  РЕЗУЛЬТАТ")
    print("=" * 50)
    fs = result.get('fill_stats', {})
    print(f"  Всего рядов: {fs.get('total_rows', 0)}")
    print(f"  🟢 Свободно: {fs.get('green', 0)}")
    print(f"  🟡 Средне: {fs.get('yellow', 0)}")
    print(f"  🔴 Полно: {fs.get('red', 0)}")
    print(f"  Средняя заполненность: {fs.get('avg_fill_pct', 0)}%")
    print(f"\n  Рекомендация: {result.get('recommend', 'N/A')}")

    # Ручной подсчёт для сверки
    print("\n✅ Сверка с ручным подсчётом:")
    exp_free = input("  Ожидалось свободно: ").strip()
    exp_med = input("  Ожидалось средне: ").strip()
    exp_full = input("  Ожидалось полно: ").strip()

    # Расчёт точности
    accuracy_note = ""
    if exp_free:
        actual_free = fs.get('green', 0)
        diff = abs(int(exp_free) - actual_free)
        if diff == 0:
            accuracy_note = f"✓ Точно по свободным ({actual_free})"
        else:
            accuracy_note = f"⚠ Расхождение: ожидалось {exp_free}, показано {actual_free} (разница: {diff})"

    # Сохранение
    test_data = {
        "test_num": test_num,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "location": location,
        "notes": notes,
        "screenshots": [os.path.basename(p) if p else None for p in screenshots],
        "result": result,
        "expected_free": exp_free or None,
        "expected_medium": exp_med or None,
        "expected_full": exp_full or None,
        "accuracy_note": accuracy_note
    }

    print("\n💾 Сохранение...")
    save_log(test_data)
    save_results_txt(test_data)

    print("\n" + "=" * 50)
    print("  Тест завершён!")
    print("=" * 50)


def view_stats():
    """Показать статистику по всем тестам"""
    if not os.path.exists(LOG_FILE):
        print("\n📊 Лог-файл пуст. Сначала проведите тесты.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        if not log_data:
            print("\n📊 Лог пуст.")
            return

        print("\n" + "=" * 50)
        print("  СТАТИСТИКА ТЕСТОВ")
        print("=" * 50)
        print(f"  Всего тестов: {len(log_data)}")

        # По складам
        locations = {}
        for t in log_data:
            loc = t.get('location', 'unknown')
            locations[loc] = locations.get(loc, 0) + 1

        print("\n  По складам:")
        for loc, cnt in sorted(locations.items()):
            print(f"    {loc}: {cnt} тестов")

        # Последние 5 тестов
        print("\n  Последние 5 тестов:")
        for t in log_data[-5:]:
            fs = t.get('result', {}).get('fill_stats', {})
            print(f"    #{t.get('test_num')} | {t.get('location')} | "
                  f"🟢{fs.get('green', 0)} 🟡{fs.get('yellow', 0)} 🔴{fs.get('red', 0)}")

        # Расширенная аналитика
        print("\n" + "=" * 50)
        print("  РАСШИРЕННАЯ АНАЛИТИКА")
        print("=" * 50)

        # Точность
        accurate_count = sum(1 for t in log_data if t.get('accuracy_note', '').startswith('✓'))
        mismatch_count = sum(1 for t in log_data if t.get('accuracy_note', '').startswith('⚠'))
        total_with_check = accurate_count + mismatch_count

        if total_with_check > 0:
            accuracy_pct = accurate_count / total_with_check * 100
            print(f"  Точных совпадений: {accurate_count}/{total_with_check} ({accuracy_pct:.1f}%)")
            print(f"  Расхождений: {mismatch_count}")

        # Средняя заполненность по всем тестам
        avg_fill_sum = 0
        fill_count = 0
        for t in log_data:
            fs = t.get('result', {}).get('fill_stats', {})
            if 'avg_fill_pct' in fs:
                avg_fill_sum += fs['avg_fill_pct']
                fill_count += 1

        if fill_count > 0:
            print(f"  Средняя заполненность: {avg_fill_sum / fill_count:.1f}%")

        # Распределение по заполненности
        low_fill = sum(1 for t in log_data if t.get('result', {}).get('fill_stats', {}).get('avg_fill_pct', 100) < 30)
        med_fill = sum(1 for t in log_data if 30 <= t.get('result', {}).get('fill_stats', {}).get('avg_fill_pct', 0) < 70)
        high_fill = sum(1 for t in log_data if t.get('result', {}).get('fill_stats', {}).get('avg_fill_pct', 0) >= 70)

        print(f"\n  Распределение по заполненности:")
        print(f"    Низкая (<30%): {low_fill} тестов")
        print(f"    Средняя (30-70%): {med_fill} тестов")
        print(f"    Высокая (≥70%): {high_fill} тестов")

    except Exception as e:
        print(f"\n📊 Ошибка чтения статистики: {e}")


def export_report():
    """Экспорт отчёта в формате для руководства"""
    if not os.path.exists(LOG_FILE):
        print("\n📄 Лог-файл пуст. Нечего экспортировать.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        if not log_data:
            print("\n📄 Лог пуст.")
            return

        # Считаем точность
        accurate_count = sum(1 for t in log_data if t.get('accuracy_note', '').startswith('✓'))
        total_with_check = sum(1 for t in log_data if t.get('accuracy_note', ''))

        accuracy_pct = (accurate_count / total_with_check * 100) if total_with_check > 0 else 0

        # Формируем отчёт
        report = f"""
============================================================
ОТЧЁТ ПО ТЕСТИРОВАНИЮ MEZONI VISION
Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M')}
============================================================

1. ОБЩАЯ СТАТИСТИКА
   Протестировано: {len(log_data)} тестов
   Уникальных локаций: {len(set(t.get('location', '') for t in log_data))}

2. ТОЧНОСТЬ АНАЛИЗА
   Точных совпадений: {accurate_count}/{total_with_check} ({accuracy_pct:.1f}%)
   Расхождений: {total_with_check - accurate_count}

3. РЕКОМЕНДАЦИЯ
"""

        if accuracy_pct >= 90:
            report += "   ✅ ГОТОВО К ПИЛОТНОМУ ВНЕДРЕНИЮ\n"
        elif accuracy_pct >= 70:
            report += "   ⚠ ТРЕБУЕТСЯ ДОРАБОТКА АЛГОРИТМА\n"
        else:
            report += "   ❌ НЕ ГОТОВО. НУЖНА КАЛИБРОВКА\n"

        report += """
4. ПОДРОБНОСТИ ПО ТЕСТАМ
"""

        for t in log_data:
            fs = t.get('result', {}).get('fill_stats', {})
            report += f"""
--- Тест #{t.get('test_num')} ---
Локация: {t.get('location')}
Дата: {t.get('timestamp')}
Результат: 🟢{fs.get('green', 0)} 🟡{fs.get('yellow', 0)} 🔴{fs.get('red', 0)}
Заполненность: {fs.get('avg_fill_pct', 0)}%
Точность: {t.get('accuracy_note', 'не сверялось')}
"""

        # Сохраняем
        report_file = "test_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 Отчёт сохранён: {report_file}")
        print("\n" + "=" * 50)
        print(report)

    except Exception as e:
        print(f"\n📄 Ошибка экспорта отчёта: {e}")


if __name__ == "__main__":
    print("\n  mezoni-vision TEST LOG")
    print("  =====================")

    if not check_server():
        print("\n  Подсказка: запусти mezoni-vision.exe и попробуй снова")
        exit(1)

    print("\n  1 - Новый тест")
    print("  2 - Показать статистику")
    print("  3 - Экспорт отчёта")
    choice = input("\n  Выбор (1/2/3): ").strip()

    if choice == "2":
        view_stats()
    elif choice == "3":
        export_report()
    else:
        run_test()
