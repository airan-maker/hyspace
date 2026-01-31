"""
Seed Data Loader

SeedDataAgent가 생성한 데이터를 실제 DB에 적용하는 로더.
모델별 매핑 및 중복 체크 포함.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    ProcessNode,
    IPBlock,
    FabEquipment,
    WIPItem,
    Material,
    Supplier,
    WaferRecord,
    YieldEvent,
    Equipment,
)


class SeedDataLoader:
    """시드 데이터를 DB에 적용"""

    def __init__(self, db: Session):
        self.db = db

    def load_all(self, data: dict, clear_existing: bool = False) -> dict:
        """전체 시드 데이터 로드"""
        result = {}

        if clear_existing:
            result["cleared"] = self.clear_all()

        result["process_nodes"] = self._load_process_nodes(data.get("process_nodes", []))
        result["ip_blocks"] = self._load_ip_blocks(data.get("ip_blocks", []))
        result["fab_equipment"] = self._load_fab_equipment(data.get("fab_equipment", []))
        result["wip_items"] = self._load_wip_items(data.get("wip_items", []))
        result["materials"] = self._load_materials(data.get("materials", []))
        result["suppliers"] = self._load_suppliers(data.get("suppliers", []))
        result["wafer_records"] = self._load_wafer_records(data.get("wafer_records", []))
        result["yield_events"] = self._load_yield_events(data.get("yield_events", []))

        self.db.commit()
        return result

    # ----------------------------------------------------------
    # Process Nodes
    # ----------------------------------------------------------
    def _load_process_nodes(self, nodes: list[dict]) -> dict:
        created, skipped = 0, 0
        for n in nodes:
            existing = self.db.query(ProcessNode).filter(
                ProcessNode.name == n["name"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = ProcessNode(
                name=n["name"],
                node_nm=n["node_nm"],
                wafer_cost=n["wafer_cost"],
                defect_density=n["defect_density"],
                base_core_area=n["base_core_area"],
                cache_density=n["cache_density"],
                io_area_per_lane=n["io_area_per_lane"],
                scaling_factor=n.get("scaling_factor", 1.0),
                power_density=n["power_density"],
                max_frequency_ghz=n["max_frequency_ghz"],
                is_active=n.get("is_active", True),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # IP Blocks
    # ----------------------------------------------------------
    def _load_ip_blocks(self, blocks: list[dict]) -> dict:
        created, skipped = 0, 0
        for b in blocks:
            existing = self.db.query(IPBlock).filter(
                IPBlock.name == b["name"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = IPBlock(
                name=b["name"],
                type=b["type"],
                vendor=b.get("vendor"),
                version=b.get("version"),
                area_mm2=b["area_mm2"],
                power_mw=b["power_mw"],
                performance_metric=b.get("performance_metric"),
                performance_unit=b.get("performance_unit"),
                silicon_proven=b.get("silicon_proven", False),
                description=b.get("description"),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Fab Equipment
    # ----------------------------------------------------------
    def _load_fab_equipment(self, equipment: list[dict]) -> dict:
        created, skipped = 0, 0
        for e in equipment:
            existing = self.db.query(FabEquipment).filter(
                FabEquipment.equipment_id == e["equipment_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = FabEquipment(
                equipment_id=e["equipment_id"],
                name=e["name"],
                equipment_type=e["equipment_type"],
                bay=e.get("bay"),
                capacity_wph=e.get("capacity_wph"),
                oee=e.get("oee"),
                availability=e.get("availability"),
                performance=e.get("performance"),
                quality=e.get("quality"),
                mtbf_hours=e.get("mtbf_hours"),
                mttr_hours=e.get("mttr_hours"),
                status=e.get("status", "IDLE"),
                last_maintenance=_parse_dt(e.get("last_maintenance")),
                next_maintenance=_parse_dt(e.get("next_maintenance")),
                specs=e.get("specs"),
                process_capabilities=e.get("process_capabilities"),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # WIP Items
    # ----------------------------------------------------------
    def _load_wip_items(self, items: list[dict]) -> dict:
        created, skipped = 0, 0
        for w in items:
            existing = self.db.query(WIPItem).filter(
                WIPItem.lot_id == w["lot_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = WIPItem(
                lot_id=w["lot_id"],
                product_id=w["product_id"],
                wafer_count=w["wafer_count"],
                current_step=w.get("current_step", 1),
                total_steps=w["total_steps"],
                current_operation=w.get("current_operation"),
                priority=w.get("priority", 5),
                due_date=_parse_dt(w.get("due_date")),
                estimated_completion=_parse_dt(w.get("estimated_completion")),
                current_bay=w.get("current_bay"),
                status=w.get("status", "QUEUED"),
                hold_reason=w.get("hold_reason"),
                start_time=_parse_dt(w.get("start_time")),
                route=w.get("route"),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Materials
    # ----------------------------------------------------------
    def _load_materials(self, materials: list[dict]) -> dict:
        created, skipped = 0, 0
        for m in materials:
            existing = self.db.query(Material).filter(
                Material.material_id == m["material_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = Material(
                material_id=m["material_id"],
                name=m["name"],
                category=m["category"],
                current_stock=m.get("current_stock", 0),
                unit=m.get("unit"),
                safety_stock=m.get("safety_stock"),
                reorder_point=m.get("reorder_point"),
                max_stock=m.get("max_stock"),
                unit_cost=m.get("unit_cost"),
                lead_time_days=m.get("lead_time_days"),
                lead_time_min=m.get("lead_time_min"),
                lead_time_max=m.get("lead_time_max"),
                criticality=m.get("criticality"),
                substitute_available=m.get("substitute_available", False),
                daily_consumption=m.get("daily_consumption"),
                monthly_consumption=m.get("monthly_consumption"),
                specifications=m.get("specifications"),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Suppliers
    # ----------------------------------------------------------
    def _load_suppliers(self, suppliers: list[dict]) -> dict:
        created, skipped = 0, 0
        seen = set()
        for s in suppliers:
            sid = s["supplier_id"]
            if sid in seen:
                skipped += 1
                continue
            seen.add(sid)

            existing = self.db.query(Supplier).filter(
                Supplier.supplier_id == sid
            ).first()
            if existing:
                skipped += 1
                continue

            obj = Supplier(
                supplier_id=sid,
                name=s["name"],
                tier=s["tier"],
                country=s.get("country"),
                region=s.get("region"),
                lead_time_days=s.get("lead_time_days"),
                on_time_delivery_rate=s.get("on_time_delivery_rate"),
                quality_rating=s.get("quality_rating"),
                risk_score=s.get("risk_score"),
                geopolitical_exposure=s.get("geopolitical_exposure"),
                contract_status=s.get("contract_status"),
                certifications=s.get("certifications"),
                is_active=True,
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Wafer Records
    # ----------------------------------------------------------
    def _load_wafer_records(self, records: list[dict]) -> dict:
        created, skipped = 0, 0
        for r in records:
            existing = self.db.query(WaferRecord).filter(
                WaferRecord.wafer_id == r["wafer_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = WaferRecord(
                wafer_id=r["wafer_id"],
                lot_id=r["lot_id"],
                product_id=r.get("product_id"),
                process_step=r.get("process_step"),
                equipment_id=r.get("equipment_id"),
                yield_percent=r.get("yield_percent"),
                die_count=r.get("die_count"),
                good_die_count=r.get("good_die_count"),
                defect_count=r.get("defect_count"),
                sensor_data=r.get("sensor_data"),
                metrology_data=r.get("metrology_data"),
                defect_map=r.get("defect_map"),
                process_start=_parse_dt(r.get("process_start")),
                process_end=_parse_dt(r.get("process_end")),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Yield Events
    # ----------------------------------------------------------
    def _load_yield_events(self, events: list[dict]) -> dict:
        created, skipped = 0, 0
        for e in events:
            existing = self.db.query(YieldEvent).filter(
                YieldEvent.event_id == e["event_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            obj = YieldEvent(
                event_id=e["event_id"],
                title=e["title"],
                description=e.get("description"),
                status=e.get("status", "OPEN"),
                severity=e.get("severity"),
                yield_drop_percent=e.get("yield_drop_percent"),
                affected_wafer_count=e.get("affected_wafer_count"),
                process_step=e.get("process_step"),
                equipment_ids=e.get("equipment_ids"),
                root_causes=e.get("root_causes"),
                analysis_summary=e.get("analysis_summary"),
                recommendations=e.get("recommendations"),
                detected_at=_parse_dt(e.get("detected_at")),
                resolved_at=_parse_dt(e.get("resolved_at")),
            )
            self.db.add(obj)
            created += 1

        return {"created": created, "skipped": skipped}

    # ----------------------------------------------------------
    # Status & Clear
    # ----------------------------------------------------------
    def get_status(self) -> dict:
        """현재 DB 데이터 상태"""
        return {
            "process_nodes": self.db.query(ProcessNode).count(),
            "ip_blocks": self.db.query(IPBlock).count(),
            "fab_equipment": self.db.query(FabEquipment).count(),
            "wip_items": self.db.query(WIPItem).count(),
            "materials": self.db.query(Material).count(),
            "suppliers": self.db.query(Supplier).count(),
            "wafer_records": self.db.query(WaferRecord).count(),
            "yield_events": self.db.query(YieldEvent).count(),
        }

    def clear_all(self) -> dict:
        """전체 시드 데이터 삭제 (역순으로 FK 의존성 해소)"""
        counts = {}

        # 역순 삭제 (FK 의존성)
        tables = [
            ("yield_events", YieldEvent),
            ("wafer_records", WaferRecord),
            ("wip_items", WIPItem),
            ("fab_equipment", FabEquipment),
            ("suppliers", Supplier),
            ("materials", Material),
            ("ip_blocks", IPBlock),
            ("process_nodes", ProcessNode),
        ]

        for name, model in tables:
            count = self.db.query(model).delete()
            counts[name] = count

        self.db.commit()
        return counts


def _parse_dt(value) -> datetime | None:
    """ISO 문자열 → datetime"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None
