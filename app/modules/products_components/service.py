"""Business logic for products & components."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.clients_auth.dependencies import CurrentClient
from app.modules.company_branches.repository import CompanyBranchRepository
from app.modules.products_components.dependencies import audit_from_current
from app.modules.products_components.models import (
    Component,
    ComponentBranchQuantity,
    Product,
    ProductBranchQuantity,
    ProductComponent,
)
from app.modules.products_components.repository import ProductsComponentsRepository
from app.modules.products_components.schemas import (
    BranchQuantityCreate,
    BranchQuantityUpdate,
    ComponentCreate,
    ComponentUpdate,
    ProductComponentCreate,
    ProductComponentUpdate,
    ProductCreate,
    ProductUpdate,
    component_read_dict,
    product_read_dict,
)
from app.modules.companies.service import CompanyService
from app.modules.company_branches.dependencies import ensure_client_company_access
from app.modules.company_branches.dependencies import is_company_insider


class ProductsComponentsService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ProductsComponentsRepository(db)
        self._branches = CompanyBranchRepository(db)

    def _ensure_company_access(self, current: CurrentClient, company_id: str) -> None:
        ensure_client_company_access(self._db, current, company_id)

    def _ensure_branch_in_company(self, company_id: str, branch_id: str) -> None:
        branch = self._branches.get_branch(branch_id)
        if branch is None or str(branch.company_id) != str(company_id):
            raise ValueError("Branch not found for this company.")

    def _get_component_for_company(
        self,
        company_id: str,
        component_id: str,
        *,
        active_only: bool = True,
    ) -> Component | None:
        row = self._repo.get_component(component_id)
        if row is None or str(row.company_id) != str(company_id):
            return None
        if active_only and not row.is_active:
            return None
        return row

    def _get_product_for_company(
        self,
        company_id: str,
        product_id: str,
        *,
        active_only: bool = True,
    ) -> Product | None:
        row = self._repo.get_product(product_id)
        if row is None or str(row.company_id) != str(company_id):
            return None
        if active_only and not row.is_active:
            return None
        return row

    def _apply_audit_update(self, row: Component | Product, current: CurrentClient) -> None:
        actor_type, actor_id = audit_from_current(current)
        row.updated_by_type = actor_type
        row.updated_by_id = actor_id

    # --- Components ---

    def list_components(self, company_id: str, current: CurrentClient) -> list[Component]:
        self._ensure_company_access(current, company_id)
        return self._repo.list_components(company_id)

    def list_components_paginated(
        self,
        company_id: str,
        current: CurrentClient,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Component], int] | None:
        """Paginated active components; ``None`` if company does not exist."""
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        skip = (page - 1) * page_size
        return self._repo.list_components_paginated(company_id, skip=skip, limit=page_size)

    def get_component(
        self,
        company_id: str,
        component_id: str,
        current: CurrentClient,
    ) -> Component | None:
        self._ensure_company_access(current, company_id)
        return self._get_component_for_company(company_id, component_id)

    def create_component(
        self,
        company_id: str,
        current: CurrentClient,
        data: ComponentCreate,
        *,
        main_image_url: str | None = None,
    ) -> Component:
        self._ensure_company_access(current, company_id)
        actor_type, actor_id = audit_from_current(current)
        image = main_image_url if main_image_url is not None else data.main_image
        row = Component(
            company_id=company_id,
            name_ar=data.name_ar,
            name_other=data.name_other,
            description_ar=data.description_ar,
            description_other=data.description_other,
            main_image=image,
            created_by_type=actor_type,
            created_by_id=actor_id,
            updated_by_type=actor_type,
            updated_by_id=actor_id,
            is_active=True,
        )
        try:
            return self._repo.create_component(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create component.") from e

    def update_component(
        self,
        company_id: str,
        component_id: str,
        current: CurrentClient,
        data: ComponentUpdate,
        *,
        main_image_url: str | None = None,
    ) -> Component | None:
        row = self.get_component(company_id, component_id, current)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if main_image_url is not None:
            row.main_image = main_image_url
            payload.pop("main_image", None)
        for k, v in payload.items():
            setattr(row, k, v)
        self._apply_audit_update(row, current)
        try:
            return self._repo.update_component(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update component.") from e

    def delete_component(
        self,
        company_id: str,
        component_id: str,
        current: CurrentClient,
    ) -> bool:
        row = self._repo.get_component(component_id)
        if row is None or str(row.company_id) != str(company_id):
            return False
        self._ensure_company_access(current, company_id)
        row.is_active = False
        self._apply_audit_update(row, current)
        self._repo.update_component(row)
        return True

    # --- Products ---

    def list_products(self, company_id: str, current: CurrentClient) -> list[Product]:
        self._ensure_company_access(current, company_id)
        return self._repo.list_products(company_id)

    def list_products_paginated(
        self,
        company_id: str,
        current: CurrentClient | None,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int, bool] | None:
        """
        Paginated product list for a company.

        Returns ``None`` if the company does not exist, else ``(items, total, insider)``.
        Insiders (owner / company employee) see all active products including hidden ones.
        Public callers only see ``show_product=true`` and prices respect ``show_price``.
        """
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            return None
        insider = is_company_insider(self._db, current, company_id)
        if insider and current is not None:
            self._ensure_company_access(current, company_id)
        skip = (page - 1) * page_size
        items, total = self._repo.list_products_paginated(
            company_id,
            skip=skip,
            limit=page_size,
            active_only=True,
            visible_to_public_only=not insider,
        )
        return items, total, insider

    def get_product(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
    ) -> Product | None:
        self._ensure_company_access(current, company_id)
        return self._get_product_for_company(company_id, product_id)

    def get_product_detail(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
    ) -> dict | None:
        self._ensure_company_access(current, company_id)
        row = self._repo.get_product(product_id, load_children=True)
        if row is None or str(row.company_id) != str(company_id) or not row.is_active:
            return None
        from app.modules.products_components.schemas import (
            ProductBranchQuantityRead,
            ProductComponentWithComponentRead,
        )

        insider = is_company_insider(self._db, current, company_id)
        return {
            "product": product_read_dict(row, insider=insider),
            "quantities_per_branch": [
                ProductBranchQuantityRead.model_validate(q).model_dump(mode="json")
                for q in row.branch_quantities
            ],
            "components": [
                ProductComponentWithComponentRead(
                    id=link.id,
                    product_id=link.product_id,
                    component_id=link.component_id,
                    quantity=link.quantity,
                    component=link.component,
                    created_at=link.created_at,
                    updated_at=link.updated_at,
                ).model_dump(mode="json")
                for link in row.component_links
                if link.component is not None and link.component.is_active
            ],
        }

    def create_product(
        self,
        company_id: str,
        current: CurrentClient,
        data: ProductCreate,
        *,
        main_image_url: str | None = None,
    ) -> Product:
        self._ensure_company_access(current, company_id)
        actor_type, actor_id = audit_from_current(current)
        image = main_image_url if main_image_url is not None else data.main_image
        row = Product(
            company_id=company_id,
            name_ar=data.name_ar,
            name_other=data.name_other,
            description_ar=data.description_ar,
            description_other=data.description_other,
            main_image=image,
            price=data.price,
            show_price=data.show_price,
            show_product=data.show_product,
            created_by_type=actor_type,
            created_by_id=actor_id,
            updated_by_type=actor_type,
            updated_by_id=actor_id,
            is_active=True,
        )
        try:
            return self._repo.create_product(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create product.") from e

    def update_product(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
        data: ProductUpdate,
        *,
        main_image_url: str | None = None,
    ) -> Product | None:
        row = self.get_product(company_id, product_id, current)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if main_image_url is not None:
            row.main_image = main_image_url
            payload.pop("main_image", None)
        for k, v in payload.items():
            setattr(row, k, v)
        self._apply_audit_update(row, current)
        try:
            return self._repo.update_product(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update product.") from e

    def delete_product(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
    ) -> bool:
        row = self._repo.get_product(product_id)
        if row is None or str(row.company_id) != str(company_id):
            return False
        self._ensure_company_access(current, company_id)
        row.is_active = False
        self._apply_audit_update(row, current)
        self._repo.update_product(row)
        return True

    # --- Component branch quantities ---

    def list_component_branch_quantities(
        self,
        company_id: str,
        component_id: str,
        current: CurrentClient,
    ) -> list[ComponentBranchQuantity] | None:
        if self._get_component_for_company(company_id, component_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        return self._repo.list_component_branch_quantities(component_id)

    def create_component_branch_quantity(
        self,
        company_id: str,
        component_id: str,
        current: CurrentClient,
        data: BranchQuantityCreate,
    ) -> ComponentBranchQuantity:
        if self._get_component_for_company(company_id, component_id) is None:
            raise ValueError("Component not found.")
        self._ensure_company_access(current, company_id)
        self._ensure_branch_in_company(company_id, str(data.branch_id))
        if self._repo.get_component_branch_quantity_by_pair(component_id, str(data.branch_id)):
            raise ValueError("Quantity record already exists for this component and branch.")
        row = ComponentBranchQuantity(
            component_id=component_id,
            branch_id=str(data.branch_id),
            quantity=data.quantity,
        )
        try:
            return self._repo.create_component_branch_quantity(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create component branch quantity.") from e

    def update_component_branch_quantity(
        self,
        company_id: str,
        component_id: str,
        quantity_id: str,
        current: CurrentClient,
        data: BranchQuantityUpdate,
    ) -> ComponentBranchQuantity | None:
        if self._get_component_for_company(company_id, component_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        row = self._repo.get_component_branch_quantity(quantity_id)
        if row is None or row.component_id != component_id:
            return None
        row.quantity = data.quantity
        try:
            return self._repo.update_component_branch_quantity(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update component branch quantity.") from e

    def delete_component_branch_quantity(
        self,
        company_id: str,
        component_id: str,
        quantity_id: str,
        current: CurrentClient,
    ) -> bool:
        if self._get_component_for_company(company_id, component_id) is None:
            return False
        self._ensure_company_access(current, company_id)
        row = self._repo.get_component_branch_quantity(quantity_id)
        if row is None or row.component_id != component_id:
            return False
        self._repo.delete_component_branch_quantity(row)
        return True

    # --- Product branch quantities ---

    def list_product_branch_quantities(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
    ) -> list[ProductBranchQuantity] | None:
        if self._get_product_for_company(company_id, product_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        return self._repo.list_product_branch_quantities(product_id)

    def create_product_branch_quantity(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
        data: BranchQuantityCreate,
    ) -> ProductBranchQuantity:
        if self._get_product_for_company(company_id, product_id) is None:
            raise ValueError("Product not found.")
        self._ensure_company_access(current, company_id)
        self._ensure_branch_in_company(company_id, str(data.branch_id))
        if self._repo.get_product_branch_quantity_by_pair(product_id, str(data.branch_id)):
            raise ValueError("Quantity record already exists for this product and branch.")
        row = ProductBranchQuantity(
            product_id=product_id,
            branch_id=str(data.branch_id),
            quantity=data.quantity,
        )
        try:
            return self._repo.create_product_branch_quantity(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create product branch quantity.") from e

    def update_product_branch_quantity(
        self,
        company_id: str,
        product_id: str,
        quantity_id: str,
        current: CurrentClient,
        data: BranchQuantityUpdate,
    ) -> ProductBranchQuantity | None:
        if self._get_product_for_company(company_id, product_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        row = self._repo.get_product_branch_quantity(quantity_id)
        if row is None or row.product_id != product_id:
            return None
        row.quantity = data.quantity
        try:
            return self._repo.update_product_branch_quantity(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update product branch quantity.") from e

    def delete_product_branch_quantity(
        self,
        company_id: str,
        product_id: str,
        quantity_id: str,
        current: CurrentClient,
    ) -> bool:
        if self._get_product_for_company(company_id, product_id) is None:
            return False
        self._ensure_company_access(current, company_id)
        row = self._repo.get_product_branch_quantity(quantity_id)
        if row is None or row.product_id != product_id:
            return False
        self._repo.delete_product_branch_quantity(row)
        return True

    # --- Product components ---

    def list_product_components(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
    ) -> list[ProductComponent] | None:
        if self._get_product_for_company(company_id, product_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        return self._repo.list_product_components(product_id)

    def add_product_component(
        self,
        company_id: str,
        product_id: str,
        current: CurrentClient,
        data: ProductComponentCreate,
    ) -> ProductComponent:
        if self._get_product_for_company(company_id, product_id) is None:
            raise ValueError("Product not found.")
        comp = self._get_component_for_company(company_id, str(data.component_id))
        if comp is None:
            raise ValueError("Component not found for this company.")
        self._ensure_company_access(current, company_id)
        if self._repo.get_product_component_by_pair(product_id, str(data.component_id)):
            raise ValueError("This component is already linked to the product.")
        row = ProductComponent(
            product_id=product_id,
            component_id=str(data.component_id),
            quantity=data.quantity,
        )
        try:
            created = self._repo.create_product_component(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not add component to product.") from e
        reloaded = self._repo.get_product_component(created.id)
        return reloaded or created

    def update_product_component(
        self,
        company_id: str,
        product_id: str,
        link_id: str,
        current: CurrentClient,
        data: ProductComponentUpdate,
    ) -> ProductComponent | None:
        if self._get_product_for_company(company_id, product_id) is None:
            return None
        self._ensure_company_access(current, company_id)
        row = self._repo.get_product_component(link_id)
        if row is None or row.product_id != product_id:
            return None
        row.quantity = data.quantity
        try:
            return self._repo.update_product_component(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update product component.") from e

    def delete_product_component(
        self,
        company_id: str,
        product_id: str,
        link_id: str,
        current: CurrentClient,
    ) -> bool:
        if self._get_product_for_company(company_id, product_id) is None:
            return False
        self._ensure_company_access(current, company_id)
        row = self._repo.get_product_component(link_id)
        if row is None or row.product_id != product_id:
            return False
        self._repo.delete_product_component(row)
        return True
