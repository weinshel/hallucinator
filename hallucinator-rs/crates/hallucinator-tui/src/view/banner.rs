use ratatui::layout::{Constraint, Flex, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph};
use ratatui::Frame;

use crate::theme::Theme;

const BANNER_ART: &[&str] = &[
    r"  _   _       _ _            _             _             ",
    r" | | | | __ _| | |_   _  ___(_)_ __   __ _| |_ ___  _ _ ",
    r" | |_| |/ _` | | | | | |/ __| | '_ \ / _` | __/ _ \| '_|",
    r" |  _  | (_| | | | |_| | (__| | | | | (_| | || (_) | |  ",
    r" |_| |_|\__,_|_|_|\__,_|\___|_|_| |_|\__,_|\__\___/|_|  ",
];

/// Render the startup banner as a centered overlay.
pub fn render(f: &mut Frame, theme: &Theme, tick: usize) {
    let area = f.area();

    // Don't render if terminal too narrow
    if area.width < 60 || area.height < 12 {
        return;
    }

    let popup = centered_rect(60, 10, area);

    let mut lines: Vec<Line> = Vec::new();
    lines.push(Line::from(""));

    for art_line in BANNER_ART {
        lines.push(Line::from(Span::styled(
            *art_line,
            Style::default().fg(theme.active).add_modifier(Modifier::BOLD),
        )));
    }

    lines.push(Line::from(""));

    // Subtitle with animated dots
    let dots = ".".repeat((tick % 4) + 1);
    lines.push(Line::from(Span::styled(
        format!("    Detecting hallucinated references{:<4}", dots),
        Style::default().fg(theme.dim),
    )));

    let paragraph = Paragraph::new(lines).block(
        Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(theme.active)),
    );

    f.render_widget(Clear, popup);
    f.render_widget(paragraph, popup);
}

fn centered_rect(width: u16, height: u16, area: Rect) -> Rect {
    let vertical = Layout::vertical([Constraint::Length(height)])
        .flex(Flex::Center)
        .split(area);
    Layout::horizontal([Constraint::Length(width)])
        .flex(Flex::Center)
        .split(vertical[0])[0]
}
