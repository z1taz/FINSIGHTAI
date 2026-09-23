from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from app.models.transaction import Transaction
from app.models.user import User
from app.models.case import Case, CaseStatus

class NetworkIntelligenceService:
    """
    PostgreSQL-backed Entity Relationship & Network Intelligence Engine.
    Discovers multi-hop linkages between Customers, Hardware Devices,
    IP Addresses, and Merchants without requiring a separate graph database.
    """

    async def get_network_graph(self, db: AsyncSession, limit_nodes: int = 60) -> Dict[str, Any]:
        """
        Builds a force-directed graph node-edge representation of
        Customers, Devices, IPs, and High-Risk Merchants.
        """
        nodes = []
        edges = []
        node_ids = set()

        def add_node(nid: str, label: str, ntype: str, metadata: Dict[str, Any]):
            if nid not in node_ids:
                node_ids.add(nid)
                nodes.append({
                    "id": nid,
                    "label": label,
                    "type": ntype,
                    "metadata": metadata
                })

        # 1. Fetch Users
        user_stmt = select(User).limit(20)
        user_res = await db.execute(user_stmt)
        users = user_res.scalars().all()
        for u in users:
            add_node(
                f"user_{u.id}",
                u.full_name.split()[0] if u.full_name else f"User #{u.id}",
                "customer",
                {"user_id": u.id, "email": u.email, "income": u.monthly_income}
            )

        # 2. Fetch Transactions with distinct device & ip connections
        tx_stmt = (
            select(
                Transaction.user_id,
                Transaction.device_id,
                Transaction.ip_address,
                Transaction.merchant,
                Transaction.is_fraudulent,
                Transaction.amount
            )
            .order_by(desc(Transaction.transaction_date))
            .limit(100)
        )
        tx_res = await db.execute(tx_stmt)
        txs = tx_res.all()

        device_user_counts = {}
        ip_user_counts = {}
        merchant_fraud_counts = {}

        for uid, dev, ip, merch, is_fraud, amt in txs:
            if dev:
                device_user_counts.setdefault(dev, set()).add(uid)
            if ip:
                ip_user_counts.setdefault(ip, set()).add(uid)
            if merch:
                stats = merchant_fraud_counts.setdefault(merch, {"total": 0, "fraud": 0})
                stats["total"] += 1
                if is_fraud: stats["fraud"] += 1

        # Add Device Nodes & Edges
        for dev, uids in device_user_counts.items():
            is_shared = len(uids) > 1
            dev_node_id = f"dev_{dev}"
            add_node(
                dev_node_id,
                dev,
                "device",
                {"device_id": dev, "shared_across_users": len(uids), "is_anomaly": is_shared}
            )
            for uid in uids:
                user_node_id = f"user_{uid}"
                if user_node_id in node_ids:
                    edges.append({
                        "source": user_node_id,
                        "target": dev_node_id,
                        "relationship": "AUTHENTICATED_FROM",
                        "is_risky": is_shared
                    })

        # Add IP Nodes & Edges
        for ip, uids in list(ip_user_counts.items())[:15]:
            is_shared_ip = len(uids) > 1
            ip_node_id = f"ip_{ip}"
            add_node(
                ip_node_id,
                ip,
                "ip_address",
                {"ip": ip, "connected_accounts": len(uids), "is_proxy": "185." in ip}
            )
            for uid in uids:
                user_node_id = f"user_{uid}"
                if user_node_id in node_ids:
                    edges.append({
                        "source": user_node_id,
                        "target": ip_node_id,
                        "relationship": "ROUTED_THROUGH",
                        "is_risky": is_shared_ip
                    })

        # Add High-Risk / Significant Merchant Nodes
        for merch, stats in list(merchant_fraud_counts.items())[:12]:
            fraud_rate = stats["fraud"] / stats["total"] if stats["total"] > 0 else 0
            merch_node_id = f"merch_{merch}"
            add_node(
                merch_node_id,
                merch,
                "merchant",
                {"merchant": merch, "fraud_rate_pct": round(fraud_rate * 100, 1), "high_risk": fraud_rate > 0.3}
            )

        return {
            "nodes": nodes[:limit_nodes],
            "edges": edges[:limit_nodes * 2],
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    async def detect_emerging_fraud_clusters(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Discovers emerging fraud clusters & anomaly networks (Section 10).
        Labels patterns strictly based on actual detected network metrics:
          - Shared hardware collisions (multiple accounts using identical device)
          - Proxy / VPN concentration clusters
          - Rapid velocity bursts across correlated merchant signatures
        """
        clusters = []

        # 1. Device Collisions (Multiple accounts sharing single device)
        device_collision_stmt = (
            select(
                Transaction.device_id,
                func.count(func.distinct(Transaction.user_id)).label("user_count"),
                func.count(Transaction.id).label("tx_count"),
                func.sum(Transaction.is_fraudulent).label("fraud_tx_count"),
                func.sum(Transaction.amount).label("total_volume")
            )
            .where(Transaction.device_id.isnot(None))
            .group_by(Transaction.device_id)
            .having(func.count(func.distinct(Transaction.user_id)) > 1)
            .order_by(desc("user_count"))
            .limit(5)
        )
        dev_res = await db.execute(device_collision_stmt)
        dev_rows = dev_res.all()

        for dev_id, u_count, tx_count, f_count, volume in dev_rows:
            f_count = f_count or 0
            clusters.append({
                "cluster_id": f"CLUSTER-DEV-{dev_id}",
                "cluster_type": "SHARED_HARDWARE_COLLISION",
                "label": "Multi-Account Device Collision",
                "severity": "CRITICAL" if f_count > 0 else "HIGH",
                "entity_count": int(u_count),
                "transaction_volume": float(volume or 0),
                "flagged_transactions": int(f_count),
                "description": f"Hardware fingerprint '{dev_id}' is actively shared across {u_count} distinct customer accounts with {tx_count} transactions recorded.",
                "observed_pattern": "Credential stuffing / syndicate multi-accounting",
                "recommended_action": "Quarantine device fingerprint and enforce out-of-band biometric challenge across all linked accounts."
            })

        # 2. IP Proxy Concentration Clusters
        ip_cluster_stmt = (
            select(
                Transaction.ip_address,
                Transaction.location,
                func.count(func.distinct(Transaction.user_id)).label("user_count"),
                func.count(Transaction.id).label("tx_count"),
                func.sum(Transaction.is_fraudulent).label("fraud_count")
            )
            .where(Transaction.ip_address.isnot(None))
            .group_by(Transaction.ip_address, Transaction.location)
            .having(func.count(func.distinct(Transaction.user_id)) > 1)
            .order_by(desc("tx_count"))
            .limit(5)
        )
        ip_res = await db.execute(ip_cluster_stmt)
        ip_rows = ip_res.all()

        for ip_addr, loc, u_count, tx_count, f_count in ip_rows:
            f_count = f_count or 0
            is_proxy = "Proxy" in (loc or "") or "185." in ip_addr
            clusters.append({
                "cluster_id": f"CLUSTER-IP-{ip_addr.replace('.', '-')}",
                "cluster_type": "IP_CONCENTRATION_CLUSTER",
                "label": "Correlated IP Origin Cluster",
                "severity": "CRITICAL" if is_proxy else "MEDIUM",
                "entity_count": int(u_count),
                "transaction_volume": 0.0,
                "flagged_transactions": int(f_count),
                "description": f"IP origin '{ip_addr}' ({loc or 'Unknown Locale'}) routes traffic for {u_count} distinct user accounts ({tx_count} transactions).",
                "observed_pattern": "Automated botnet routing or commercial proxy gateway",
                "recommended_action": "Apply elevated challenge verification on incoming sessions from this routing subnet."
            })

        # 3. High-Risk Merchant Velocity Rings
        merch_ring_stmt = (
            select(
                Transaction.merchant,
                Transaction.category,
                func.count(Transaction.id).label("tx_count"),
                func.sum(Transaction.is_fraudulent).label("fraud_count"),
                func.avg(Transaction.fraud_score).label("avg_risk")
            )
            .group_by(Transaction.merchant, Transaction.category)
            .having(func.sum(Transaction.is_fraudulent) >= 2)
            .order_by(desc("fraud_count"))
            .limit(5)
        )
        merch_res = await db.execute(merch_ring_stmt)
        merch_rows = merch_res.all()

        for merch, cat, tx_count, f_count, avg_risk in merch_rows:
            clusters.append({
                "cluster_id": f"CLUSTER-MERCH-{merch.replace(' ', '_')}",
                "cluster_type": "HIGH_RISK_MERCHANT_RING",
                "label": f"Elevated Merchant Concentration ({merch})",
                "severity": "HIGH",
                "entity_count": int(tx_count),
                "transaction_volume": 0.0,
                "flagged_transactions": int(f_count),
                "description": f"Merchant entity '{merch}' exhibits concentrated fraud flags ({f_count} of {tx_count} transactions flagged, avg risk score {round(float(avg_risk or 0), 1)}/100).",
                "observed_pattern": "Repeated unauthorized charge settlement",
                "recommended_action": "Notify merchant risk desk and mandate 3D-Secure authentication."
            })

        return clusters

network_intelligence = NetworkIntelligenceService()
