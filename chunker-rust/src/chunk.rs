//! Semantic chunking by lexical cohesion (a TextTiling-style approach).
//!
//! We clean the markup, split into sentences, and measure the term overlap
//! between adjacent sentences (the Otsuka-Ochiai cosine on term sets). A chunk
//! boundary is placed at a **topic shift** — a local minimum of cohesion that
//! also dips below the document's mean cohesion — or whenever a chunk would
//! exceed `max_words`. Chunks therefore break where the subject changes rather
//! than at arbitrary token counts.

use serde::Serialize;

const STOPWORDS: &[&str] = &[
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "this", "that", "these",
    "those", "as", "at", "by", "from", "we", "you", "they", "i", "he", "she",
    "his", "her", "its", "our", "your", "their", "will", "can", "do", "does",
    "if", "then", "so", "not", "no", "yes", "have", "has", "had", "how", "what",
    "when", "where", "which", "who", "into", "out", "up", "down", "over",
];

#[derive(Serialize, Debug)]
pub struct Chunk {
    pub index: usize,
    pub text: String,
    pub n_sentences: usize,
    pub cohesion: f64,
}

/// Strip common markdown/markup so cohesion is measured on prose, not syntax.
pub fn clean(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        match ch {
            '#' | '*' | '_' | '`' | '>' | '[' | ']' | '(' | ')' | '|' | '~' => out.push(' '),
            _ => out.push(ch),
        }
    }
    out
}

/// Split cleaned text into trimmed, non-empty sentences.
pub fn split_sentences(text: &str) -> Vec<String> {
    let mut sentences = Vec::new();
    let mut cur = String::new();
    for ch in text.chars() {
        if ch == '\n' {
            // treat hard line breaks as soft boundaries too
            if !cur.trim().is_empty() {
                cur.push(' ');
            }
            continue;
        }
        cur.push(ch);
        if ch == '.' || ch == '!' || ch == '?' {
            let s = cur.trim().to_string();
            if !s.is_empty() {
                sentences.push(s);
            }
            cur.clear();
        }
    }
    let tail = cur.trim().to_string();
    if !tail.is_empty() {
        sentences.push(tail);
    }
    sentences
}

/// Content terms of a sentence: lowercased, de-punctuated, stopwords removed.
pub fn terms(sentence: &str) -> Vec<String> {
    sentence
        .split(|c: char| !c.is_alphanumeric())
        .filter(|w| w.len() >= 2)
        .map(|w| w.to_lowercase())
        .filter(|w| !STOPWORDS.contains(&w.as_str()))
        .collect()
}

fn unique(v: &[String]) -> Vec<&String> {
    let mut seen = std::collections::HashSet::new();
    v.iter().filter(|w| seen.insert((*w).clone())).collect()
}

/// Otsuka-Ochiai cosine over term sets: |A∩B| / sqrt(|A|·|B|).
pub fn cohesion(a: &[String], b: &[String]) -> f64 {
    let ua = unique(a);
    let ub = unique(b);
    if ua.is_empty() || ub.is_empty() {
        return 0.0;
    }
    let set_a: std::collections::HashSet<&String> = ua.iter().copied().collect();
    let inter = ub.iter().filter(|w| set_a.contains(*w)).count();
    inter as f64 / ((ua.len() * ub.len()) as f64).sqrt()
}

fn word_count(sentences: &[String]) -> usize {
    sentences.iter().map(|s| s.split_whitespace().count()).sum()
}

/// Chunk `text` at topic shifts, capping each chunk at `max_words`.
pub fn chunk(text: &str, max_words: usize) -> Vec<Chunk> {
    let cleaned = clean(text);
    let sentences = split_sentences(&cleaned);
    if sentences.is_empty() {
        return vec![];
    }
    if sentences.len() == 1 {
        return vec![Chunk {
            index: 0,
            text: sentences[0].clone(),
            n_sentences: 1,
            cohesion: 1.0,
        }];
    }

    let term_lists: Vec<Vec<String>> = sentences.iter().map(|s| terms(s)).collect();
    // adjacent cohesion: coh[i] between sentence i and i+1
    let coh: Vec<f64> = (0..sentences.len() - 1)
        .map(|i| cohesion(&term_lists[i], &term_lists[i + 1]))
        .collect();

    let mean = coh.iter().sum::<f64>() / coh.len().max(1) as f64;

    // boundary after sentence i (i in 0..n-1) if coh[i] is a local min below mean
    let is_boundary = |i: usize| -> bool {
        let left = if i > 0 { coh[i - 1] } else { f64::INFINITY };
        let right = if i + 1 < coh.len() { coh[i + 1] } else { f64::INFINITY };
        coh[i] < mean && coh[i] <= left && coh[i] <= right
    };

    let mut chunks = Vec::new();
    let mut start = 0usize;
    let mut idx = 0usize;
    let mut i = 0usize;
    while i < sentences.len() {
        let cur = &sentences[start..=i];
        let over_cap = word_count(cur) >= max_words && i > start;
        let topic_shift = i < sentences.len() - 1 && i >= start && is_boundary(i);
        let last = i == sentences.len() - 1;
        if over_cap || topic_shift || last {
            let group = &sentences[start..=i];
            // mean adjacent cohesion inside the group
            let inner: Vec<f64> = (start..i).map(|j| coh[j]).collect();
            let c = if inner.is_empty() {
                1.0
            } else {
                inner.iter().sum::<f64>() / inner.len() as f64
            };
            chunks.push(Chunk {
                index: idx,
                text: group.join(" "),
                n_sentences: group.len(),
                cohesion: (c * 1000.0).round() / 1000.0,
            });
            idx += 1;
            start = i + 1;
        }
        i += 1;
    }
    chunks
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clean_strips_markdown() {
        let c = clean("# Title\n- a *bold* `code` [link](x)");
        assert!(!c.contains('#'));
        assert!(!c.contains('*'));
        assert!(!c.contains('`'));
        assert!(c.contains("Title"));
    }

    #[test]
    fn splits_sentences() {
        let s = split_sentences("Hello world. How are you? Fine!");
        assert_eq!(s.len(), 3);
    }

    #[test]
    fn cohesion_high_for_shared_terms() {
        let a = terms("database index query performance");
        let b = terms("query performance database tuning");
        let c = terms("cats kittens feline whiskers");
        assert!(cohesion(&a, &b) > 0.4);
        assert!(cohesion(&a, &c) < 0.1);
    }

    #[test]
    fn splits_on_topic_shift() {
        let text = "Cats are wonderful pets. Cats purr and cats sleep a lot. \
                    A kitten is a young cat. \
                    Databases store structured data. A database index speeds up queries. \
                    Query planners optimize database access.";
        let chunks = chunk(text, 200);
        assert!(chunks.len() >= 2, "expected a topic boundary, got {:?}", chunks.len());
        // first chunk should be about cats, a later chunk about databases
        assert!(chunks[0].text.to_lowercase().contains("cat"));
        assert!(chunks.iter().any(|c| c.text.to_lowercase().contains("database")));
    }

    #[test]
    fn respects_max_words() {
        // one coherent topic, many sentences -> capped by max_words
        let s = "alpha beta gamma delta epsilon zeta. ".repeat(20);
        let chunks = chunk(&s, 20);
        assert!(chunks.len() > 1);
        for c in &chunks {
            // each chunk is at most max_words plus the overflowing sentence
            assert!(c.text.split_whitespace().count() <= 20 + 8);
        }
    }
}
