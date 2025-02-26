from bot_main import parse_message


def test_parse_message_valid():
    """Check that parse_message returns correct dict."""
    text = 'IKEA 120.50 EUR'
    result = parse_message(text)
    expected = {'pos': 'IKEA', 'sum': 120.50, 'currency': 'EUR'}
    assert result == expected, f'Expected {expected}, got {result}'


def test_parse_message_valid_no_currency():
    """Check if parse_message defaults to EUR when no currency provided."""
    text = 'Starbucks 10.99'
    result = parse_message(text)
    assert result['pos'] == 'Starbucks'
    assert result['sum'] == 10.99
    assert result['currency'] == 'EUR', (
        'Should default to EUR if no currency is provided.'
    )


def test_parse_message_with_comma_decimal():
    """Check parsing with comma."""
    text = 'Apple 100,50 USD'
    result = parse_message(text)
    assert result['pos'] == 'Apple'
    assert result['sum'] == 100.50
    assert result['currency'] == 'USD'
