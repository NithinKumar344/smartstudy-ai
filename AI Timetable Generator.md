# AI Timetable Generator

A genetic algorithm builds clash-free timetables for every class and every teacher. It runs entirely in your browser.

## Setup

Days per week Periods per day Lunch after period

## Classes, subjects and teachers

One line per subject: Section, Subject, Teacher, Hours per week. Add “, lab” at the end for a lab, which gets 2 back-to-back periods.

## Timetable

View

How the AI works

- Each lesson (a 1-period class or a 2-period lab) is a gene. Its value is the slot it starts in, and one full timetable is a chromosome.
- Fitness counts hard clashes (two lessons for one class or one teacher in the same slot) at 100 points each. Soft penalties add points for repeating a subject on one day, free periods between classes, uneven days, and teachers with more than 5 periods in a day.
- A population of 50 timetables evolves by tournament selection, uniform crossover, elitism and a guided mutation that tries 8 new slots for a lesson and keeps the best.
- The run stops at zero penalty, after 250 generations, or when the result stops improving.