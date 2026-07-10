"""Tests for XML adapter with inline script extraction."""

from pathlib import Path
from llmwiki.adapters.xml_adapter import XMLAdapter


class TestXMLAdapter:
    def setup_method(self):
        self.adapter = XMLAdapter()

    def test_can_handle_xml(self, tmp_path):
        f = tmp_path / "workflow.xml"
        f.write_text("<Workflow/>")
        assert self.adapter.can_handle(f)

    def test_cannot_handle_java(self, tmp_path):
        f = tmp_path / "Main.java"
        f.write_text("class Main {}")
        assert not self.adapter.can_handle(f)

    def test_extract_simple_xml(self, tmp_path):
        f = tmp_path / "config.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Configuration name="TestConfig">\n'
            '  <Entry key="host" value="localhost"/>\n'
            '  <Entry key="port" value="8080"/>\n'
            '</Configuration>\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) >= 1
        assert pages[0].title == "TestConfig" or pages[0].title == "config"
        assert pages[0].language == "xml"

    def test_extract_workflow_with_beanshell(self, tmp_path):
        f = tmp_path / "MyWorkflow.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Workflow name="VF-Core-TestWorkflow">\n'
            '  <Step name="Initialize">\n'
            '    <Script>\n'
            '      <Source>\n'
            '        import sailpoint.object.Identity;\n'
            '        Identity id = context.getObjectByName(Identity.class, name);\n'
            '        return id;\n'
            '      </Source>\n'
            '    </Script>\n'
            '  </Step>\n'
            '  <Step name="Finalize">\n'
            '    <Script>\n'
            '      <Source>\n'
            '        log.debug("Done");\n'
            '      </Source>\n'
            '    </Script>\n'
            '  </Step>\n'
            '</Workflow>\n'
        )
        pages = self.adapter.extract(f, {"extract_beanshell": True})
        assert len(pages) >= 1
        parent = pages[0]
        assert "VF-Core-TestWorkflow" in parent.title or "MyWorkflow" in parent.title
        assert "Initialize" in parent.body
        bsh_pages = [p for p in pages if "beanshell" in p.category]
        if bsh_pages:
            assert any("Initialize" in p.title for p in bsh_pages)

    def test_extract_references(self, tmp_path):
        f = tmp_path / "MyRule.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Rule name="TestRule">\n'
            '  <ReferencedRules>\n'
            '    <Reference class="sailpoint.object.Rule" name="CommonLib"/>\n'
            '  </ReferencedRules>\n'
            '  <Source>\n'
            '    import com.vf.core.utility.AccountUtil;\n'
            '    AccountUtil.doSomething();\n'
            '  </Source>\n'
            '</Rule>\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) >= 1
        refs = pages[0].references
        assert any("CommonLib" in r for r in refs)

    def test_category_from_directory(self, tmp_path):
        d = tmp_path / "config" / "Workflow" / "Core"
        d.mkdir(parents=True)
        f = d / "MyWorkflow.xml"
        f.write_text('<Workflow name="Test"/>')
        pages = self.adapter.extract(f, {})
        assert pages[0].category != ""
