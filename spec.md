# Requirements Specification for `museoman`

## Documentation Management System – EPS UAM Museum, by the student association LIMA

EPS - Escuela Politécnica Superior
UAM - Universidad Autónoma de Madrid
LIMA - Laboratorio de Informática y Matemáticas

---

## 1. General Description

Web application built with Django to manage the assignment and documentation of museum items from EPS UAM, maintained by the LIMA student association.

The system allows managing items, assigning them to users, documenting them through a state workflow, and performing advanced searches.

---

## 2. Users and Roles

### User Types

- Administrators
- Regular user

### Authentication

- Login using email and password
- No public registration
- Only administrators can create users

### Rules

- Administrators can modify name and email of any user
- A user can be created as admin or non-admin

---

## 3. Museum Items

Each item has:

- nombre
- identificador (unique)
- estado
- assigned user (optional)
- comments/observations
- tipo
- vitrina (optional)
- activo (boolean for deactivation)
- creation metadata

### States

- libre
- asignado
- en revisión
- documentado

### State Rules

- libre → asignado: user or admin
- asignado → en revisión: assigned user only
- en revisión → documentado: admin only
- any state can be reverted to the previous one by the assigned user or admin

---

## 4. Types and Vitrinas

### Tipo

- Reusable classification (e.g., ordenador, disco duro)
- Created and managed only by administrators

### Vitrina

- Identified by number
- Dynamically extendable
- Default: no vitrina
- Only administrators can assign or modify

---

## 5. Photos

- Each item has multiple photos
- Administrators can add and delete photos at any time
- Stored in the server filesystem

---

## 6. Audit log

- Item status changes are logged along with the time and user who performed the action
- Log entries are sent to a discord channel through a webhook

---

## 7. Item Assignment

- One item can be assigned to only one user
- A user can have multiple items
- Assignment can be done by:
  - the user themselves
  - an administrator (to any user)

### Concurrency

- Must prevent simultaneous assignment of the same item

---

## 8. Search and Filters

Main screen with:

### Filters

- estado
- assigned user
- tipo
- vitrina
- active/inactive
- unread comments

### Features

- text search (nombre and identificador)
- combinable filters
- pagination
- sorting

---

## 9. Item Deactivation

- Items are not physically deleted
- Administrators can deactivate them
- Hidden by default in listings
- Filter available to include them

---

## 10. Dashboard

Dashboard must display:

- number of items per state
- items per user
- overall progress

---

## 11. Permissions

- Only administrators can:
  - create users
  - create items
  - assign items to other users
  - create and modify tipos
  - create and modify vitrinas
  - mark items as documentado
  - deactivate items

- Everyone can:
  - assign items to themselves
  - change state to en revisión (if assigned)
  - revert states (if assigned)

---

## 12. Interface

- Language: Spanish
- Design: minimal, lightweight, responsive
- Must include:
  - reference to EPS UAM
  - LIMA name and logo

---

## 13. Pages

- Login
- Dashboard
- Item list
- Item detail
- Project information

---

## 14. Security

- Restricted to authenticated users
- Backend permission validation
- CSRF protection
- Role-based access control

---

## 15. Database

- PostgreSQL through a configurable URL

---

## 16. Non-Functional Requirements

- Lightweight system
- Low concurrency expected
- High data consistency
- Simplicity and maintainability prioritized

---
