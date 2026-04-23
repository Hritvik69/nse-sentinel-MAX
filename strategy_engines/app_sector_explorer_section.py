from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from sector_master import (
        get_all_sectors,
        get_sector,
        get_sector_count,
        get_sector_description,
        get_sector_peers,
        get_stocks_in_sector,
        search_stock,
    )
    _SM_OK = True
    _SM_ERR = ""
except ImportError as exc:
    _SM_OK = False
    _SM_ERR = str(exc).strip() or "sector_master.py import failed"

    def get_all_sectors() -> list[str]:
        return []

    def get_sector_count() -> dict[str, int]:
        return {}

    def get_stocks_in_sector(sector_name: str) -> list[str]:
        return []

    def get_sector(symbol: str) -> str | None:
        return None

    def search_stock(query: str) -> list[tuple[str, str]]:
        return []

    def get_sector_peers(symbol: str) -> list[str]:
        return []

    def get_sector_description(sector_name: str) -> str:
        return sector_name


def render_sector_explorer_section() -> None:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<h2 style="margin-bottom:4px;">Sector Explorer</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:12px;color:#4a6480;margin-bottom:16px;">'
        "Static curated sector database · sector lookup, peers, and coverage overview."
        "</div>",
        unsafe_allow_html=True,
    )

    if not _SM_OK:
        st.warning(
            "Sector Explorer is unavailable because `sector_master.py` could not be loaded. "
            f"Import error: {_SM_ERR}"
        )
        return

    _all_sectors = get_all_sectors()
    if not _all_sectors:
        st.warning(
            "Sector Explorer did not find any configured sectors. "
            "Check the `sector_master.py` sector lists."
        )
        return

    _sector_counts = get_sector_count()
    _tab_browse, _tab_lookup, _tab_coverage = st.tabs(
        ["Browse Sectors", "Stock Lookup", "Coverage Overview"]
    )

    with _tab_browse:
        _options = [
            f"{sector_name}  ({_sector_counts.get(sector_name, 0)} stocks)"
            for sector_name in _all_sectors
        ]
        _choice = st.selectbox(
            "Select Sector",
            options=_options,
            key="se_sector_select",
        )

        if _choice:
            _sector_name = _choice.split("  (")[0].strip()
            _stocks = get_stocks_in_sector(_sector_name)
            _description = get_sector_description(_sector_name)

            st.markdown(
                f'<div style="background:#0b1017;border:1.5px solid #1e3a5f;'
                f'border-radius:12px;padding:14px 18px;margin:8px 0 16px;">'
                f'<span style="font-family:\'Syne\',sans-serif;font-size:16px;'
                f'font-weight:800;color:#ccd9e8;">{_sector_name}</span>'
                f'<span style="font-size:11px;color:#4a6480;margin-left:12px;">'
                f'{_description}</span><br>'
                f'<span style="font-size:12px;color:#8ab4d8;margin-top:6px;display:block;">'
                f'{len(_stocks)} stocks</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if _stocks:
                _col_count = 6
                _rows = [
                    _stocks[idx: idx + _col_count]
                    for idx in range(0, len(_stocks), _col_count)
                ]
                for _row in _rows:
                    _cols = st.columns(len(_row))
                    for _col, _symbol in zip(_cols, _row):
                        _col.markdown(
                            f'<div style="background:#0f1923;border:1px solid #1e3a5f;'
                            f'border-radius:8px;padding:6px 10px;text-align:center;'
                            f'font-size:11px;font-weight:700;color:#ccd9e8;">'
                            f'{_symbol}</div>',
                            unsafe_allow_html=True,
                        )

                with st.expander("Plain list", expanded=False):
                    st.code(", ".join(_stocks), language=None)
            else:
                st.info("No stocks are configured for this sector.")

    with _tab_lookup:
        _lookup_col1, _lookup_col2 = st.columns([3, 2])

        with _lookup_col1:
            _symbol_input = st.text_input(
                "Enter stock symbol",
                placeholder="e.g. HDFCBANK or partial: HDFC",
                key="se_symbol_input",
            ).strip().upper()

        with _lookup_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            _search_btn = st.button("Find Sector", key="se_search_btn")

        if _search_btn and _symbol_input:
            _exact_sector = get_sector(_symbol_input)
            if _exact_sector:
                _peers = get_sector_peers(_symbol_input)
                st.success(
                    f"**{_symbol_input}** → Primary Sector: **{_exact_sector}**  "
                    f"({get_sector_description(_exact_sector)})"
                )
                if _peers:
                    st.markdown(
                        f'<div style="font-size:12px;color:#8ab4d8;margin:8px 0 4px;">'
                        f'Sector Peers ({len(_peers)} stocks):</div>',
                        unsafe_allow_html=True,
                    )
                    st.write(", ".join(_peers))
            else:
                _matches = search_stock(_symbol_input)
                if _matches:
                    st.info(
                        f"No exact match for '{_symbol_input}'. "
                        f"Found {len(_matches)} partial match(es)."
                    )
                    _match_df = pd.DataFrame(_matches, columns=["Symbol", "Sector"])
                    _match_df["Description"] = _match_df["Sector"].apply(
                        get_sector_description
                    )
                    st.dataframe(
                        _match_df,
                        width="stretch",
                        hide_index=True,
                    )
                else:
                    st.warning(
                        f"'{_symbol_input}' was not found in `sector_master.py`. "
                        "Check the symbol spelling or update the sector map."
                    )

    with _tab_coverage:
        _total_count = sum(_sector_counts.values())
        st.markdown(
            f'<div style="font-size:13px;color:#8ab4d8;margin-bottom:12px;">'
            f'Total coverage: <b style="color:#00d4a8;">{_total_count} stocks</b> '
            f'across <b style="color:#00d4a8;">{len(_sector_counts)} sectors</b></div>',
            unsafe_allow_html=True,
        )

        _coverage_rows = [
            {
                "Sector": sector_name,
                "Description": get_sector_description(sector_name),
                "Stocks": _sector_counts.get(sector_name, 0),
            }
            for sector_name in _all_sectors
        ]
        _coverage_df = pd.DataFrame(_coverage_rows)

        st.dataframe(
            _coverage_df,
            column_config={
                "Sector": st.column_config.TextColumn("Sector"),
                "Description": st.column_config.TextColumn("Description"),
                "Stocks": st.column_config.NumberColumn("# Stocks", format="%d"),
            },
            width="stretch",
            hide_index=True,
        )
