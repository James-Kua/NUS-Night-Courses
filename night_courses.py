import asyncio
import aiohttp
import requests
import time
from datetime import datetime
from fpdf import FPDF

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

async def fetch_course(session, moduleCode):
    url = f"https://api.nusmods.com/v2/2023-2024/modules/{moduleCode}.json"
    async with session.get(url) as response:
        try:
            return await response.json()
        except Exception as e:
            print(f"Error processing module {moduleCode}: {e}")
            return None

async def process_modules(modules):
    night_courses_by_semester = {1: [], 2: [], 3: [], 4: []}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_course(session, module['moduleCode']) for module in modules]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                for semester in result['semesterData']:
                    all_lectures = [lesson for lesson in semester['timetable'] if lesson['lessonType'] in lectureLessonTypes]
                    filtered_lectures = [lesson for lesson in semester['timetable'] if int(lesson['startTime']) >= 1800 and lesson['lessonType'] in lectureLessonTypes]
                    all_tutorial = [lesson for lesson in semester['timetable'] if lesson['lessonType'] in tutorialLessonTypes]
                    filtered_tutorial = [lesson for lesson in semester['timetable'] if int(lesson['startTime']) >= 1800 and lesson['lessonType'] in tutorialLessonTypes]
                    if (not all_lectures or any(filtered_lectures)) and (not all_tutorial or any(filtered_tutorial)) and (any(all_lectures) or any(all_tutorial)):
                        night_courses_by_semester[semester['semester']].append(f"{result['moduleCode']} [{result['moduleCredit']} Units]: {result['title']}")


    return night_courses_by_semester

def print_courses_by_semester(courses_by_semester):
    for semester, courses in courses_by_semester.items():
        print(f"Semester {semester}: {len(courses)} courses")
        for course in courses:
            print(course)
        print()

def export_to_pdf(courses_by_semester):
    today = datetime.now().strftime("%d_%b")
    outputFile = f"NUS_Night_Courses_CAA_{today}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for semester, courses in courses_by_semester.items():
        pdf.add_page()
        pdf.set_font("Arial", size=9)
        pdf.cell(200, 10, f"Semester {semester}: {len(courses)} courses", ln=True, align="C")
        pdf.ln(10)
        for course in courses:
            try:
                course = course.encode("ascii", "ignore").decode("ascii")
                pdf.multi_cell(0, 10, course)
                pdf.ln(5)
            except Exception as e:
                print(f"Error encoding course: {e}")
    pdf.output(outputFile)

async def main():
    response = requests.get('https://api.nusmods.com/v2/2023-2024/moduleInfo.json')
    data = response.json()
    courses_by_semester = await process_modules(data)
    print_courses_by_semester(courses_by_semester)
    export_to_pdf(courses_by_semester)

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print("--- %s seconds ---" % (time.time() - start_time))
