# Orderflow Project Working Report

## 1. Project purpose

This project is a small FastAPI-based backend for managing users, products, and inventory. Its main job is to let clients:

- register and log in users
- create products
- create inventory entries for products
- increase stock for existing inventory
- protect certain routes with JWT authentication and role-based access

The project is designed in layers so the code stays organized and easier to maintain.

---

## 2. High-level architecture

The project follows a common backend pattern:

1. Routes layer
   - receives requests
   - validates input through schemas
   - calls services

2. Service layer
   - contains business rules
   - decides if operations are allowed
   - coordinates repositories

3. Repository layer
   - talks to the database
   - performs create/read/update operations

4. Models layer
   - defines database tables and relationships

5. Schemas layer
   - defines request and response shapes
   - makes the API predictable

6. Core and dependency helpers
   - handle security, config, DB session, and auth checks

Why this structure exists:
- it separates concerns
- it makes debugging easier
- it allows business logic to be tested independently
- it keeps the API endpoints clean and simple

---

## 3. Folder-by-folder mapping

### Root files

#### [alembic.ini](alembic.ini)
- Purpose: configuration file for Alembic migrations.
- Why it exists: it tells Alembic how to connect to the database and where migration scripts are stored.

#### [requirements.txt](requirements.txt)
- Purpose: lists all Python dependencies for the project.
- Why it exists: it lets anyone install the same packages in a clean environment.

#### [docker-compose.yml](docker-compose.yml)
- Purpose: starts a PostgreSQL container.
- Why it exists: it gives the app a local database without needing a manual server setup.

#### [tests/test_inventory_stock.py](tests/test_inventory_stock.py)
- Purpose: tests stock increase behavior.
- Why it exists: it confirms that adding stock updates inventory quantity correctly.

---

## 4. Application code mapping

### [app/main.py](app/main.py)

#### Function: health_check()
- Purpose: returns a simple health/status response at the root endpoint.
- Why it exists: it helps confirm the API is running.

#### App setup
- The FastAPI app is created here.
- All routers are included here.
- Why: this file acts as the main entry point for the application.

---

## 5. API routes and methods

### [app/api/v1/routes/auth.py](app/api/v1/routes/auth.py)

#### Function: register_user()
- Purpose: handles user registration.
- Why: it exposes a public endpoint for new users.
- Flow:
  - receives user data from the request
  - calls the user service to create the user
  - returns the created user record

#### Function: login()
- Purpose: authenticates a user and issues a JWT token.
- Why: the app needs a secure way to identify users after registration.
- Flow:
  - reads username/password from the login form
  - validates the credentials
  - creates a token containing the user id
  - returns the token to the client

---

### [app/api/v1/routes/users.py](app/api/v1/routes/users.py)

#### Function: get_me()
- Purpose: returns the currently authenticated user.
- Why: it gives the client a simple way to fetch their own profile.

#### Function: admin_test()
- Purpose: demonstrates a role-protected route.
- Why: it shows how access control is enforced for admin users.

---

### [app/api/v1/routes/products.py](app/api/v1/routes/products.py)

#### Function: create_product()
- Purpose: creates a new product.
- Why: products are the main catalog entity in the system.
- Flow:
  - accepts the product payload
  - checks the current user has admin/staff permission
  - creates a ProductRepository and ProductService
  - calls the service to create the product

---

### [app/api/v1/routes/inventory.py](app/api/v1/routes/inventory.py)

#### Function: create_inventory()
- Purpose: creates an inventory record for a product.
- Why: inventory is tracked separately from the product itself so stock can be managed independently.
- Flow:
  - accepts inventory data
  - verifies that the product exists
  - creates inventory if it does not already exist

#### Function: add_stock()
- Purpose: increases stock quantity for an existing inventory entry.
- Why: this is the main stock-changing operation in the business workflow.
- Flow:
  - finds inventory using the product id
  - updates quantity
  - saves the change

---

## 6. Authentication and authorization layer

### [app/api/dependecies/auth.py](app/api/dependecies/auth.py)

#### Function: get_current_user()
- Purpose: extracts the current user from the JWT token.
- Why: it allows protected routes to know who is making the request.

#### Function: get_current_active_user()
- Purpose: checks whether the current user is active.
- Why: inactive accounts should not be allowed to use protected features.

#### Function: required_roles(*roles)
- Purpose: returns a dependency that checks if the user has one of the allowed roles.
- Why: it centralizes role-based access control.

---

## 7. Security helpers

### [app/core/security.py](app/core/security.py)

#### Function: hash_password()
- Purpose: securely hashes passwords.
- Why: raw passwords should never be stored in the database.

#### Function: verify_password()
- Purpose: checks a plain password against the stored hash.
- Why: it allows login validation.

#### Function: create_access_token()
- Purpose: creates a JWT token for authentication.
- Why: the API uses stateless authentication, so each request can verify identity using a token.

#### Function: decode_access_token()
- Purpose: reads and validates a JWT token.
- Why: it is used by the auth dependency to identify the current user.

---

## 8. Database connection layer

### [app/db/session.py](app/db/session.py)

#### Function: get_db()
- Purpose: provides a database session for each request.
- Why: FastAPI route functions need a database session to query and save data safely.

### [app/db/base.py](app/db/base.py)

#### Class: Base
- Purpose: base class for all SQLAlchemy models.
- Why: it lets SQLAlchemy manage model metadata in one place.

---

## 9. Models and database tables

### [app/models/user.py](app/models/user.py)

#### Class: User
- Purpose: represents the users table.
- Why: it maps the database structure to Python objects.
- Important fields:
  - id
  - email
  - hashed_password
  - full_name
  - role
  - is_active
  - created_at / updated_at

### [app/models/product.py](app/models/product.py)

#### Class: Product
- Purpose: represents the products table.
- Why: products need their own table because the catalog is separate from stock tracking.
- Important fields:
  - sku
  - name
  - description
  - price
  - category
  - is_active

### [app/models/inventory.py](app/models/inventory.py)

#### Class: Inventory
- Purpose: represents the inventory table.
- Why: stock is stored separately from product attributes so inventory can change without changing the product record.
- Important fields:
  - product_id
  - quantity
  - reserved_quantity

### [app/models/enums.py](app/models/enums.py)

#### Enum: UserRole
- Purpose: defines allowed roles: ADMIN, STAFF, CUSTOMER.
- Why: role-based access control needs a fixed set of values.

---

## 10. Repositories

Repositories are responsible for database operations only.

### [app/repositories/product_repository.py](app/repositories/product_repository.py)

#### Class: ProductRepository

#### Method: create()
- Purpose: adds and saves a product.
- Why: it keeps the database save logic in one place.

#### Method: get_by_id()
- Purpose: fetches a product by id.
- Why: other layers can reuse this lookup.

#### Method: get_by_sku()
- Purpose: fetches a product by SKU.
- Why: duplicate SKU validation depends on this.

#### Method: get_all()
- Purpose: fetches active products.
- Why: it gives a clean list of non-deactivated products.

#### Method: deactivate()
- Purpose: marks a product inactive.
- Why: the app uses soft deactivation instead of hard deletion.

### [app/repositories/inventory_repository.py](app/repositories/inventory_repository.py)

#### Class: InventoryRepository

#### Method: create()
- Purpose: creates inventory records.
- Why: inventory persistence is isolated from service rules.

#### Method: get_by_product_id()
- Purpose: finds inventory by product id.
- Why: stock updates are tied to the product.

#### Method: update()
- Purpose: commits inventory changes.
- Why: the service can update an object and hand it off to the repository.

#### Method: get_by_id()
- Purpose: gets inventory by its own id.
- Why: it is useful for direct lookups.

---

## 11. Services

Services contain the business rules.

### [app/services/product_service.py](app/services/product_service.py)

#### Class: ProductService

#### Method: create_product()
- Purpose: creates a product if the SKU is unique.
- Why: this prevents duplicate products from being created.
- Logic:
  - checks if SKU exists
  - raises an error if it does
  - creates a Product model instance
  - saves it through the repository

### [app/services/inventory_service.py](app/services/inventory_service.py)

#### Class: InventoryService

#### Method: create_inventory()
- Purpose: creates inventory for a valid product.
- Why: inventory should only exist for a real product, and duplicates should be blocked.
- Logic:
  - checks whether the product exists
  - checks whether inventory already exists
  - creates inventory if valid

#### Method: add_stock()
- Purpose: increases stock quantity for an inventory record.
- Why: this encodes the business rule that stock grows by adding to the current balance.

---

## 12. Schemas

Schemas define the API contract.

### [app/schemas/user.py](app/schemas/user.py)

#### Class: UserCreate
- Purpose: validates user registration input.
- Why: it ensures the email format and password length are acceptable.

#### Class: UserResponse
- Purpose: defines the shape returned for user data.
- Why: the API response is consistent and safe.

#### Class: UserLogin
- Purpose: validates login input shape.
- Why: login endpoints need a predictable input model.

### [app/schemas/product.py](app/schemas/product.py)

#### Class: ProductCreate
- Purpose: validates create-product input.
- Why: it ensures product values are correctly formatted.

#### Class: ProductResponse
- Purpose: defines the output shape for products.
- Why: clients know what fields to expect.

### [app/schemas/inventory.py](app/schemas/inventory.py)

#### Class: InventoryCreate
- Purpose: validates inventory creation payload.
- Why: it ensures product id and quantity are valid.

#### Class: InventoryResponse
- Purpose: defines inventory response data.
- Why: API responses stay consistent.

#### Class: StockOperation
- Purpose: validates quantity for stock updates.
- Why: it prevents invalid stock operations.

### [app/schemas/token.py](app/schemas/token.py)

#### Class: TokenResponse
- Purpose: defines the token response model.
- Why: the login endpoint returns a predictable token structure.

---

## 13. Database migrations

The project uses Alembic to manage schema changes.

### [alembic/versions/26a19d006580_create_users_table.py](alembic/versions/26a19d006580_create_users_table.py)
- Creates the users table.
- Why: user authentication needs a stored user record.

### [alembic/versions/4dd85d57b797_add_user_role.py](alembic/versions/4dd85d57b797_add_user_role.py)
- Adds the role column and enum.
- Why: access control requires user roles.

### [alembic/versions/6b705143fadb_create_products_table.py](alembic/versions/6b705143fadb_create_products_table.py)
- Creates the products table.
- Why: products need a persistent catalog table.

### [alembic/versions/f9ae485c5af4_create_inventory_table.py](alembic/versions/f9ae485c5af4_create_inventory_table.py)
- Creates the inventory table.
- Why: stock tracking requires its own table linked to products.

### [alembic/env.py](alembic/env.py)
- Connects Alembic to the app models and database settings.
- Why: migrations need to know the app’s database configuration.

---

## 14. Request flow examples

### A. User registration flow
1. Client calls /auth/register.
2. auth route receives the data.
3. create_user() in the user service runs.
4. The service checks whether the email already exists.
5. If valid, the password is hashed.
6. User is stored in the database.
7. The response returns the new user object.

Why this flow exists:
- it keeps registration logic separate from route handling
- it ensures duplicate accounts are prevented

### B. Login flow
1. Client calls /auth/login.
2. The auth route uses authenticate_user().
3. The service finds the user and checks the password.
4. If valid, a JWT is created.
5. The token is returned to the client.

Why this flow exists:
- it allows secure, stateless authentication.

### C. Product creation flow
1. Client calls /products.
2. The route checks that the user has admin/staff access.
3. The service validates the SKU.
4. If valid, a new product is saved.

Why this flow exists:
- the app needs a protected catalog management path.

### D. Inventory add-stock flow
1. Client calls /inventory/{product_id}/add-stock.
2. The route uses InventoryService.
3. The service looks up inventory for the product.
4. The quantity is increased.
5. The updated inventory is saved.

Why this flow exists:
- this is the core stock-management action.

---

## 15. Why the project is organized this way

- Routes are thin because they should only handle HTTP concerns.
- Services hold business rules because those rules are more important than transport details.
- Repositories isolate database code because persistence logic should be reusable and easy to change.
- Schemas define contracts because the API should validate data before it reaches business logic.
- Models map database tables because the app needs a Python representation of its data.
- Security helpers centralize auth logic because authentication should be consistent across the entire project.

---

## 16. Practical summary

If you want to understand the project quickly, think of it in this order:

- Start with [app/main.py](app/main.py) to see the app entry point.
- Read the routes in [app/api/v1/routes](app/api/v1/routes) to see what endpoints exist.
- Follow the route into the service layer in [app/services](app/services) to understand business logic.
- Look at repositories in [app/repositories](app/repositories) to see database operations.
- Review models in [app/models](app/models) to understand the database structure.
- Check [app/core/security.py](app/core/security.py) and [app/api/dependecies/auth.py](app/api/dependecies/auth.py) for authentication.

---

## 17. Short conclusion

This project is a simple but well-structured FastAPI backend. It uses:

- FastAPI for API endpoints
- SQLAlchemy for database access
- Alembic for schema migrations
- JWT for authentication
- role-based access control for protected routes

Its design is intentionally layered so each part has one clear responsibility.
