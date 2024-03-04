import asyncio
import aiohttp
import requests
import time
from datetime import datetime
from openpyxl import Workbook

# All lecture types
lectureLessonTypes = [
    'Lecture',
    'Design Lecture',
    'Packaged Lecture',
    'Seminar-Style Module Class',
    'Sectional Teaching',
]

# All tutorial types
tutorialLessonTypes = [
    'Laboratory',
    'Recitation',
    'Tutorial',
    'Tutorial Type 2',
    'Workshop'
]

async def fetch_course(session, moduleCode, academic_year):
    url = f"https://api.nusmods.com/v2/{academic_year}/modules/{moduleCode}.json"
    async with session.get(url) as response:
        try:
            return await response.json()
        except Exception as e:
            print(f"Error processing module {moduleCode}: {e}")
            return None

async def process_modules(modules, academic_year):
    night_courses_by_semester = {1: [], 2: [], 3: [], 4: []}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_course(session, module['moduleCode'], academic_year) for module in modules]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                for semester in result['semesterData']:
                    all_lectures = [lesson for lesson in semester['timetable'] if lesson['lessonType'] in lectureLessonTypes]
                    filtered_lectures = [lesson for lesson in semester['timetable'] if int(lesson['startTime']) >= 1800 and lesson['lessonType'] in lectureLessonTypes]
                    all_tutorial = [lesson for lesson in semester['timetable'] if lesson['lessonType'] in tutorialLessonTypes]
                    filtered_tutorial = [lesson for lesson in semester['timetable'] if int(lesson['startTime']) >= 1800 and lesson['lessonType'] in tutorialLessonTypes]
                    if (not all_lectures or any(filtered_lectures)) and (not all_tutorial or any(filtered_tutorial)) and (any(all_lectures) or any(all_tutorial)):
                        night_courses_by_semester[semester['semester']].append([result['moduleCode'], result['moduleCredit'], result['title']])
    return night_courses_by_semester

def create_worksheet(workbook, semester, courses):
    worksheet = workbook.create_sheet(title=f"Semester {semester}")
    worksheet['A1'] = 'Code'
    worksheet['B1'] = 'Units'
    worksheet['C1'] = 'Name'

    for idx, course_info in enumerate(courses, start=2):
        module_code, credit_units, course_name = course_info
        worksheet.cell(row=idx, column=1, value=module_code.strip())
        worksheet.cell(row=idx, column=2, value=float(credit_units.strip()))
        worksheet.cell(row=idx, column=3, value=course_name.strip())

async def main():
    academic_year = '2023-2024'
    response = requests.get(f'https://api.nusmods.com/v2/{academic_year}/moduleInfo.json')
    data = response.json()
    courses_by_semester = await process_modules(data, academic_year)

    workbook = Workbook()
    for semester, courses in courses_by_semester.items():
        create_worksheet(workbook, semester, courses)

    today = datetime.now().strftime("%d_%b")
    output_file = f"NUS_Night_Courses_{academic_year}_CAA_{today}.xlsx"
    del workbook['Sheet']
    workbook.save(output_file)

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print("--- %s seconds ---" % (time.time() - start_time))

