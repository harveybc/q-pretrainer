import pytest
from unittest.mock import patch, MagicMock
from importlib.metadata import EntryPoint
from app.plugin_loader import load_plugin, load_encoder_decoder_plugins, get_plugin_params

def test_load_plugin_success():
    mock_entry_point = MagicMock()
    mock_entry_point.name = 'mock_plugin'
    mock_entry_point.load.return_value = MagicMock(plugin_params={'param1': 'value1'})
    mock_entry_points = {'feature_extractor.encoders': [mock_entry_point]}

    with patch('importlib.metadata.entry_points', return_value=mock_entry_points):
        plugin_class, required_params = load_plugin('feature_extractor.encoders', 'mock_plugin')
        assert plugin_class.plugin_params == {'param1': 'value1'}
        assert required_params == ['param1']
        mock_entry_point.load.assert_called_once()

def test_load_plugin_key_error():
    with patch('importlib.metadata.entry_points', return_value={'feature_extractor.encoders': []}):
        with pytest.raises(ImportError) as excinfo:
            load_plugin('feature_extractor.encoders', 'nonexistent_plugin')
        assert 'Plugin nonexistent_plugin not found in group feature_extractor.encoders.' in str(excinfo.value)

def test_load_plugin_general_exception():
    with patch('importlib.metadata.entry_points', side_effect=Exception('General error')):
        with pytest.raises(Exception) as excinfo:
            load_plugin('feature_extractor.encoders', 'mock_plugin')
        assert 'General error' in str(excinfo.value)

def test_load_encoder_decoder_plugins():
    mock_encoder_entry_point = MagicMock()
    mock_encoder_entry_point.name = 'mock_encoder'
    mock_encoder_entry_point.load.return_value = MagicMock(plugin_params={'param1': 'value1'})

    mock_decoder_entry_point = MagicMock()
    mock_decoder_entry_point.name = 'mock_decoder'
    mock_decoder_entry_point.load.return_value = MagicMock(plugin_params={'param2': 'value2'})

    mock_entry_points = {
        'feature_extractor.encoders': [mock_encoder_entry_point],
        'feature_extractor.decoders': [mock_decoder_entry_point]
    }

    with patch('importlib.metadata.entry_points', return_value=mock_entry_points):
        encoder_plugin, encoder_params, decoder_plugin, decoder_params = load_encoder_decoder_plugins('mock_encoder', 'mock_decoder')
        assert encoder_plugin.plugin_params == {'param1': 'value1'}
        assert encoder_params == ['param1']
        assert decoder_plugin.plugin_params == {'param2': 'value2']
        assert decoder_params == ['param2']
        mock_encoder_entry_point.load.assert_called_once()
        mock_decoder_entry_point.load.assert_called_once()

def test_get_plugin_params_success():
    mock_entry_point = MagicMock()
    mock_entry_point.name = 'mock_plugin'
    mock_entry_point.load.return_value = MagicMock(plugin_params={'param1': 'value1'})
    mock_entry_points = {'feature_extractor.encoders': [mock_entry_point]}

    with patch('importlib.metadata.entry_points', return_value=mock_entry_points):
        params = get_plugin_params('feature_extractor.encoders', 'mock_plugin')
        assert params == {'param1': 'value1'}
        mock_entry_point.load.assert_called_once()

def test_get_plugin_params_key_error():
    with patch('importlib.metadata.entry_points', return_value={'feature_extractor.encoders': []}):
        params = get_plugin_params('feature_extractor.encoders', 'nonexistent_plugin')
        assert params == {}

def test_get_plugin_params_general_exception():
    with patch('importlib.metadata.entry_points', side_effect=Exception('General error')):
        params = get_plugin_params('feature_extractor.encoders', 'mock_plugin')
        assert params == {}
