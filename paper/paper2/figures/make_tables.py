"""Write paper/paper2/figures/items_table.tex: the 54 items (English gloss by the author/Claude, not a validated
translation), the thesis's expected 'common-sense' answer, and LLM item means from the analysis outputs (read-only).

    python3 paper/paper2/figures/make_tables.py
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
I1 = os.path.join(ROOT, "sim/society/tools/survey/out/items.csv")
I2 = os.path.join(ROOT, "sim/society/tools/survey/out_exp2/items.csv")

GLOSS = {
    "A01": "Watching a film still in cinemas after finding it posted online",
    "A02": "Making the data of a DVD one bought viewable by anyone online",
    "A03": "Posting images of a favourite celebrity on one's blog without permission",
    "A04": "Copying a detailed web page verbatim and submitting it as a report",
    "A05": "Using someone else's smartphone to buy paid lottery items in a game app",
    "A06": "Looking through someone's phone address book without permission to learn about their acquaintances",
    "A07": "Scanning part of a book one owns and making it viewable by anyone online",
    "A08": "Downloading music from a commercial CD for free from an individual's website",
    "A09": "Downloading a live video of a favourite singer that someone uploaded to YouTube",
    "A10": "Copying commercial software onto DVD or CD",
    "A11": "Photographing only the needed pages of a book in a bookshop instead of buying it",
    "A12": "Photographing the contents of a library book",
    "A13": "Selling counterfeit brand bags or watches in an online auction",
    "A14": "Using someone else's mobile phone for a call without particularly asking",
    "A15": "Giving someone's phone number or e-mail address to others without permission",
    "A16": "Asking for and using a colleague's PC password at work",
    "A17": "Sending the data of a purchased music CD to a friend (cloud or CD-R)",
    "A18": "Making derivative works without permission (character paint on one's car, cosplay)",
    "A19": "Using a Wi-Fi password one learned by chance to connect one's PC",
    "A20": "Posting a photo showing strangers' faces to one's SNS or web page as is",
    "A21": "Using CC instead of BCC when e-mailing many people",
    "A22": "Scanning an interesting magazine page and e-mailing it to a friend",
    "A23": "Posting a photo taken with a friend on one's SNS without the friend's permission",
    "A24": "Complaining about work on one's web page, naming another person",
    "A25": "Using a PC on which someone else is still logged in to Google or Yahoo!",
    "A26": "Following a chain mail's request to forward it to many people",
    "A27": "Happening to see someone typing their PC password",
    "A28": "Making one's own copy of goods seen on TV or in town, after looking them up",
    "A29": "Posting an opinion from someone else's blog verbatim on one's own blog",
    "A30": "Registering for an app a friend recommended on SNS without checking it",
    "A31": "Giving one's own auction item a better rating than it deserves",
    "A32": "Picking arguments in a group chat to drive out someone who disagrees",
    "A33": "Joining others in a group chat in criticising someone without understanding the issue",
    "A34": "Dubbing a DVD rented from a video shop at home",
    "A35": "Criticising a restaurant as bad on one's blog",
    "B01": "Copying another person's report verbatim when given the chance",
    "B02": "Copying answers seen on another person's sheet during a test",
    "B03": "Keeping something borrowed and not returning it",
    "B04": "Telling a mutual friend a friend's personal details (birthday, address) when asked",
    "B05": "Drawing or pasting Disney characters on one's pencil board or notebook",
    "B06": "Joining others at school or work in criticising someone without understanding the issue",
    "B07": "Throwing away New Year cards and letters as they are",
    "B08": "Throwing away a mail-order box with the shipping label still attached",
    "B09": "Taking office supplies home because one needs them",
    "B10": "Keeping a CD borrowed from a friend because they have not asked for it",
    "B11": "Not having returned clothes borrowed when staying over at a friend's",
    "B12": "Passing off an opinion heard from someone else as one's own",
    "B13": "Picking and eating fruit from a tree in a neighbour's garden",
    "B14": "Writing a memo on a public-toilet wall during an urgent call (only a pen at hand)",
    "B15": "Walking past when the person ahead drops what look like documents",
    "B16": "Taking an empty seat on a crowded bus or train without hesitation",
    "B17": "Sometimes playing loud music late at night",
    "B18": "Often forgetting to return library books",
    "B19": "Forgetting to return a DVD rented from a video shop",
}


def main():
    r1 = {r["item"]: r for r in csv.DictReader(open(I1, encoding="utf-8"))}
    r2 = {r["item"]: r for r in csv.DictReader(open(I2, encoding="utf-8"))}
    out = [r"\begin{longtable}{@{}l>{\raggedright\arraybackslash}p{0.50\textwidth}rrrrr@{}}",
           r"\caption{The 54 items (English gloss; the questionnaire was administered in Japanese), the thesis's expected "
           r"``common-sense'' answer (norm; 5 = serious problem, 1 = no problem at all), and LLM item means. "
           r"$\dagger$ = gray-zone item (14). C0/C4: Experiment 1 without persona (Sonnet/Opus, $n=30$); "
           r"C1: Big Five words (Sonnet, $n=100$); D1: life circumstances (Sonnet, $n=100$).}"
           r"\label{tab:items}\\",
           r"\toprule", r"Item & Behaviour & Norm & C0 & C4 & C1 & D1 \\", r"\midrule", r"\endfirsthead",
           r"\toprule", r"Item & Behaviour & Norm & C0 & C4 & C1 & D1 \\", r"\midrule", r"\endhead"]
    for i, g in GLOSS.items():
        a, b = r1[i], r2[i]
        dag = r"$^\dagger$" if a["gray"] == "1" else ""
        norm = float(a["norm"])
        ns = f"{norm:.1f}" if norm != int(norm) else f"{int(norm)}"
        out.append(f"{i}{dag} & {g} & {ns} & {float(a['C0_mean']):.2f} & {float(a['C4_mean']):.2f} & "
                   f"{float(a['C1_mean']):.2f} & {float(b['D1_mean']):.2f} \\\\")
    out += [r"\bottomrule", r"\end{longtable}"]
    open(os.path.join(HERE, "items_table.tex"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("ok")


if __name__ == "__main__":
    main()
