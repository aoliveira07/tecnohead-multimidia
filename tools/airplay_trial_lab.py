"""Offline Windows lab for controlled TecnoHead AirPlay/Casa experiments.

This tool never contacts Home Assistant, sends AirPlay packets, or changes a
receiver. It produces only option plans supported by the current RC9 App.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

TECNOHEAD_FEATURES = "0x401C4A00,0x5C340"
WIIM_FEATURES = "0x445F8A00,0x1C340"
DENON_FEATURES = "0x445F8A00,0x801C340"
ZONES = ("kitchen", "pool")


@dataclass(frozen=True)
class Scenario:
    label: str
    legacy_metadata: bool
    forward_mediaremote: bool
    note: str


SCENARIOS = {
    "B0": Scenario("Base", False, False, "Sem mudança experimental; referência do Casa."),
    "M1": Scenario(
        "Now Playing + comandos",
        False,
        True,
        "Mantém a máscara nativa e encaminha eventos RC somente na zona escolhida.",
    ),
    "M2": Scenario(
        "Metadados clássicos",
        True,
        False,
        "Pede arte/progresso clássicos ao emissor; não encaminha RC.",
    ),
    "M3": Scenario(
        "Clássicos + RC",
        True,
        True,
        "Combinação isolada. Em RC5 não chegaram eventos Now Playing enriquecidos; "
        "não presumir que haverá algo para retransmitir.",
    ),
}

FEATURE_NAMES = {
    9: "AirPlay audio",
    11: "audio redundante",
    14: "FairPlay",
    15: "capa clássica",
    16: "progresso clássico",
    17: "Now Playing clássico",
    22: "desconhecido",
    26: "autenticação MFi",
    30: "anúncio unificado",
    38: "controle unificado",
    40: "áudio em buffer",
    41: "PTP",
    46: "pareamento/acesso HomeKit",
    47: "não documentado no comparativo",
    48: "pareamento/encriptação CoreUtils",
    50: "Now Playing bplist",
    58: "Hangdog Remote Control (restrito por classe)",
    59: "stream connection setup",
}


def parse_features(value: str) -> int:
    """Decode the low-32,high-32 order of an AirPlay TXT `features` value."""
    parts = value.split(",")
    if len(parts) != 2:
        raise ValueError("features deve conter dois blocos: 0xBAIXO,0xALTO")
    try:
        low, high = (int(part.strip(), 16) for part in parts)
    except ValueError as exc:
        raise ValueError("features deve conter apenas blocos hexadecimais") from exc
    if not 0 <= low <= 0xFFFFFFFF or not 0 <= high <= 0xFFFFFFFF:
        raise ValueError("cada bloco de features deve ter no máximo 32 bits")
    return low | (high << 32)


def feature_bits(value: int) -> set[int]:
    if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("features fora do intervalo de 64 bits")
    return {bit for bit in range(64) if value & (1 << bit)}


def feature_diff(reference: str, candidate: str) -> dict[str, list[int]]:
    baseline = feature_bits(parse_features(reference))
    target = feature_bits(parse_features(candidate))
    return {"added": sorted(target - baseline), "removed": sorted(baseline - target)}


def option_plan(scenario_id: str, zone: str) -> dict[str, str]:
    """Return only existing RC9 options; never enable a vendor/MFi mask."""
    if scenario_id not in SCENARIOS:
        raise ValueError("cenário desconhecido")
    if zone not in ZONES:
        raise ValueError("zona desconhecida; uma zona por ensaio")
    scenario = SCENARIOS[scenario_id]
    return {
        "apple_legacy_metadata_zone": zone if scenario.legacy_metadata else "off",
        "apple_feature_comparison_zone": "off",
        "apple_mediaremote_forward_zone": zone if scenario.forward_mediaremote else "off",
    }


def comparison_text() -> str:
    lines = ["Comparação histórica de anúncios (não é uma leitura ao vivo):"]
    for label, value in (("WiiM", WIIM_FEATURES), ("Denon", DENON_FEATURES)):
        delta = feature_diff(TECNOHEAD_FEATURES, value)
        def describe(bits: list[int]) -> str:
            return ", ".join(f"{bit} ({FEATURE_NAMES.get(bit, 'não identificado')})" for bit in bits) or "nenhum"
        lines.append(f"{label}: adiciona {describe(delta['added'])}; remove {describe(delta['removed'])}.")
    lines.extend(
        [
            "O bit 26 anuncia MFi; a máscara conjunta RC7 levou a POST /auth-setup e falha de conexão.",
            (
                "Ícone e cartão Casa são observações distintas. Modelo/classificação e suporte real "
                "também importam; igualdade de máscara não prova controles."
            ),
            "Este laboratório não oferece bit 26/51/58, identidade Apple/comercial nem máscara arbitrária.",
        ]
    )
    return "\n".join(lines)


def observation(scenario_id: str, zone: str, states: dict[str, bool]) -> dict[str, object]:
    expected = {
        "discovered", "speaker_icon", "sender_metadata", "hk_access", "rc_event_open",
        "rc_ack", "home_art", "home_controls",
    }
    if set(states) != expected or any(type(value) is not bool for value in states.values()):
        raise ValueError("observação incompleta ou inválida")
    return {
        "schema": 1,
        "recorded_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "scenario": scenario_id,
        "zone": zone,
        "options": option_plan(scenario_id, zone),
        "observed": states,
        "home_native_success": states["home_art"] and states["home_controls"],
        "note": "Relato visual/manual; não mede comandos físicos nem autentica o peer RC.",
    }


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("TecnoHead — laboratório AirPlay/Casa (offline)")
    root.geometry("900x690")
    root.minsize(760, 590)
    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Ensaios no mesmo acessório AirPlay 2", font=("Segoe UI", 15, "bold")).pack(anchor="w")
    ttk.Label(
        frame,
        text="Planeja e registra; NÃO altera HAOS, não publica anúncios nem captura músicas.",
    ).pack(anchor="w", pady=(0, 10))

    choices = ttk.Frame(frame)
    choices.pack(fill="x")
    zone_var = tk.StringVar(value="pool")
    scenario_var = tk.StringVar(value="B0")
    ttk.Label(choices, text="Zona (uma por vez):").grid(row=0, column=0, sticky="w")
    ttk.Combobox(choices, textvariable=zone_var, values=ZONES, state="readonly", width=12).grid(
        row=0, column=1, padx=8
    )
    ttk.Label(choices, text="Cenário:").grid(row=0, column=2, padx=(18, 0))
    ttk.Combobox(
        choices, textvariable=scenario_var, values=tuple(SCENARIOS), state="readonly", width=8
    ).grid(row=0, column=3, padx=8)

    output = tk.Text(frame, height=13, wrap="word")
    output.pack(fill="both", expand=True, pady=(12, 8))
    output.configure(state="disabled")

    def refresh(*_args: object) -> None:
        scenario_id = scenario_var.get()
        zone = zone_var.get()
        text = (
            f"{scenario_id} — {SCENARIOS[scenario_id].label}\n"
            f"{SCENARIOS[scenario_id].note}\n\n"
            f"Opções RC9 para aplicar manualmente no Supervisor:\n"
            f"{json.dumps(option_plan(scenario_id, zone), indent=2, ensure_ascii=False)}\n\n"
            f"{comparison_text()}\n\n"
            "Antes de um ensaio: backup, TV livre, janela curta e opção RC desligada ao terminar. "
            "Não remover/readicionar acessórios sem autorização separada."
        )
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", text)
        output.configure(state="disabled")

    zone_var.trace_add("write", refresh)
    scenario_var.trace_add("write", refresh)
    refresh()

    def copy_plan() -> None:
        root.clipboard_clear()
        root.clipboard_append(json.dumps(option_plan(scenario_var.get(), zone_var.get()), indent=2))
        messagebox.showinfo("Plano copiado", "Opções copiadas. A aplicação no HAOS é manual.")

    ttk.Button(frame, text="Copiar opções", command=copy_plan).pack(anchor="w")
    ttk.Label(frame, text="Resultado observado no iPhone/Casa (sem nomes de faixas):").pack(
        anchor="w", pady=(14, 3)
    )
    labels = {
        "discovered": "Destino visível no AirPlay",
        "speaker_icon": "Ícone de alto-falante semelhante ao WiiM/Denon",
        "sender_metadata": "Emissor entregou Now Playing",
        "hk_access": "flags bit 10 / HK Access Control ativo nesta sessão",
        "rc_event_open": "Conexão RC com event port concluída",
        "rc_ack": "ACK de Now Playing/Commands no RC (não é UI)",
        "home_art": "Capa/faixa visíveis no próprio Casa",
        "home_controls": "Botões ativos no próprio Casa",
    }
    states = {key: tk.BooleanVar(value=False) for key in labels}
    grid = ttk.Frame(frame)
    grid.pack(anchor="w", fill="x")
    for index, (key, label) in enumerate(labels.items()):
        ttk.Checkbutton(grid, text=label, variable=states[key]).grid(
            row=index // 2, column=index % 2, sticky="w", padx=(0, 20), pady=2
        )

    def save_result() -> None:
        record = observation(
            scenario_var.get(), zone_var.get(), {key: value.get() for key, value in states.items()}
        )
        filename = f"airplay-{record['scenario']}-{record['zone']}-{datetime.now():%Y%m%d-%H%M%S}.json"
        selected = filedialog.asksaveasfilename(
            title="Salvar observação sanitizada",
            initialfile=filename,
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not selected:
            return
        try:
            with Path(selected).open("x", encoding="utf-8") as handle:
                json.dump(record, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        except FileExistsError:
            messagebox.showerror("Arquivo existente", "Escolha outro nome; nada foi sobrescrito.")
            return
        except OSError as exc:
            messagebox.showerror("Falha ao salvar", str(exc))
            return
        messagebox.showinfo("Registrado", "Observação salva localmente, sem dados de mídia.")

    ttk.Button(frame, text="Salvar observação", command=save_result).pack(anchor="w", pady=12)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", action="store_true", help="comparar máscaras históricas")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), help="emitir plano JSON")
    parser.add_argument("--zone", choices=ZONES, default="pool", help="zona do plano")
    args = parser.parse_args()
    if args.compare:
        print(comparison_text())
    if args.scenario:
        print(json.dumps(option_plan(args.scenario, args.zone), indent=2))
    if not args.compare and not args.scenario:
        launch_gui()


if __name__ == "__main__":
    main()
